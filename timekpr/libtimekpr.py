"""Library for Timekpr-nExT remote control functionality."""

import os
import re

import humanize
import yaml
from fabric import Connection
from gotify import Gotify
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError

# Load configuration from YAML file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(project_root, "conf.yaml")

with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def get_config():
    """Get the trackme configuration."""
    return config["trackme"]


def send_alert(user, action, seconds, computer, ssh, type):
    """Send alert notification via Gotify."""
    for alerts in config["gotify"]:
        if alerts["enabled"] is True:
            gotify = Gotify(
                base_url=alerts["url"],
                app_token=alerts["token"],
            )
            try:
                usage = get_usage(user, computer, ssh)
                added = humanize.naturaldelta(seconds)
                time_unused = humanize.precisedelta(usage["time_left"])
                time_used = humanize.precisedelta(usage["time_spent"])
                playtime_unused = humanize.precisedelta(usage["playtime_left"])
                playtime_used = humanize.precisedelta(usage["playtime_spent"])
                result = gotify.create_message(
                    f"{action} {added} {type}, time {time_unused} unused, {time_used} used, playtime {playtime_unused} unused, {playtime_used} used",
                    title=f"Timekpr: {user} {action} {added} {type}",
                    priority=2,
                )
            except Exception as e:
                print(f"Failed to call Gotify. Config is: {alerts}.  Error is: {e}")
                continue
            print(f"Gotify alert {result} sent to {alerts['url']}")
    return True


def get_usage(user, computer, ssh):
    """Get time usage information for a user on a computer."""
    global timekpra_userinfo_output
    fail_json = {"time_left": 0, "time_spent": 0, "result": "fail"}
    try:
        timekpra_userinfo_output = str(ssh.run(config["ssh"]["timekpra_bin"] + " --userinfo " + user, hide=True))
    except NoValidConnectionsError:
        print(f"Cannot connect to SSH server on host '{computer}'. Check address in conf.yaml or try again later.")
        return fail_json
    except AuthenticationException:
        print(
            f"Wrong credentials for user '{config['ssh']['user']}' on host '{computer}'. "
            "Check `ssh_user` and `ssh_password` credentials in conf.yaml."
        )
        return fail_json
    except Exception as e:
        quit(f"Error logging in as user '{config['ssh']['user']}' on host '{computer}', check conf.yaml. \n\n\t" + str(e))
        return fail_json
    search = r"(TIME_LEFT_DAY: )([0-9]+)"
    time_left = re.search(search, timekpra_userinfo_output)
    search = r"(TIME_SPENT_DAY: )([0-9]+)"
    time_spent = re.search(search, timekpra_userinfo_output)
    search = r"(PLAYTIME_LEFT_DAY: )([0-9]+)"
    playtime_left = re.search(search, timekpra_userinfo_output)
    search = r"(PLAYTIME_SPENT_DAY: )([0-9]+)"
    playtime_spent = re.search(search, timekpra_userinfo_output)
    if not time_left or not time_left.group(2):
        print("Error getting time left, setting to 0. ssh call result: " + str(timekpra_userinfo_output))
        return fail_json
    else:
        time_left = str(time_left.group(2))
        time_spent = str(time_spent.group(2))
        playtime_left = str(playtime_left.group(2))
        playtime_spent = str(playtime_spent.group(2))
        print(f"Time left for {user} at {computer}: {time_left} ({time_spent} spent)")
        print(f"Playtime left for {user} at {computer}: {playtime_left} ({playtime_spent} spent)")
        return {
            "time_left": time_left,
            "time_spent": time_spent,
            "playtime_left": playtime_left,
            "playtime_spent": playtime_spent,
            "result": "success",
        }


def get_connection(computer):
    """Establish SSH connection to a computer."""
    global connection
    connect_kwargs = {"allow_agent": False, "look_for_keys": False, "password": config["ssh"]["password"]}
    try:
        connection = Connection(host=computer, user=config["ssh"]["user"], connect_kwargs=connect_kwargs)
    except AuthenticationException:
        quit(
            f"Wrong credentials for user '{config['ssh']['user']}' on host '{computer}'. "
            f"Check `ssh_user` and `ssh_password` credentials in conf.yaml."
        )
    except Exception as e:
        quit(f"Error logging in as user '{config['ssh']['user']}' on host '{computer}', check conf.yaml. \n\n\t" + str(e))
    finally:
        return connection


def adjust_time(up_down_string, seconds, ssh, user, computer, type="time"):
    """Adjust time or playtime for a user."""
    adjust = "--setplaytimeleft" if type == "play" else "--settimeleft"
    command = f"{config['ssh']['timekpra_bin']} {adjust} {user} {up_down_string} {seconds}"
    print(f"Running command: {command}")
    ssh.run(command)
    if up_down_string == "-":
        action = "removed"
    else:
        action = "added"
    print(f"{action} {seconds} for user '{user}'")
    try:
        send_alert(user, action, seconds, computer, ssh, type)
    except Exception as e:
        print(f"Failed to send alert: {e}")
    return True


def increase_time(seconds, ssh, user, computer):
    """Increase time for a user."""
    return adjust_time("+", seconds, ssh, user, computer, type="time")


def decrease_time(seconds, ssh, user, computer):
    """Decrease time for a user."""
    return adjust_time("-", seconds, ssh, user, computer, type="time")


def increase_playtime(seconds, ssh, user, computer):
    """Increase playtime for a user."""
    return adjust_time("+", seconds, ssh, user, computer, type="play")


def decrease_playtime(seconds, ssh, user, computer):
    """Decrease playtime for a user."""
    return adjust_time("-", seconds, ssh, user, computer, type="play")
