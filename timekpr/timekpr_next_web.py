"""Flask web application for Timekpr-nExT remote control."""

import os

import yaml
from flask import Flask, render_template, send_from_directory

import timekpr.libtimekpr as libtimekpr

# Get the project root directory (parent of timekpr directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, "templates")
static_dir = os.path.join(project_root, "static")
config_path = os.path.join(project_root, "conf.yaml")

# Load configuration
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


def validate_request(computer: str, user: str):
    """Validate if the computer and user are in the config.

    Returns error tuple if invalid, None if valid.
    """
    # Validate if the computer and user are in the config
    if computer not in config["trackme"]:
        return {"status": "error", "message": f"Computer {computer} not found in config"}, 404
    if user not in config["trackme"][computer]:
        return {"result": "fail", "message": "user not in computer in config"}
    else:
        return {"result": "success", "message": "valid user and computer"}


@app.route("/config")
def get_config():
    """Return the trackme configuration."""
    return libtimekpr.get_config()


@app.route("/")
def index():
    """Render the main index page."""
    return render_template("index.html")


@app.route("/get_usage/<computer>/<user>")
def get_usage(computer, user):
    """Get usage statistics for a specific computer and user.

    Returns time_left, time_spent, playtime_left, playtime_spent.
    """
    if validate_request(computer, user)["result"] == "fail":
        return validate_request(computer, user), 500
    ssh = libtimekpr.get_connection(computer)
    usage = libtimekpr.get_usage(user, computer, ssh)
    return {
        "result": usage["result"],
        "time_left": usage["time_left"],
        "time_spent": usage["time_spent"],
        "playtime_left": usage.get("playtime_left", 0),
        "playtime_spent": usage.get("playtime_spent", 0),
    }, 200


@app.route("/increase_time/<computer>/<user>/<seconds>")
def increase_time(computer, user, seconds):
    """Increase time limit for a user by specified seconds.

    Returns updated time_left and time_spent on success.
    """
    if validate_request(computer, user)["result"] == "fail":
        return validate_request(computer, user), 500
    ssh = libtimekpr.get_connection(computer)
    if libtimekpr.increase_time(seconds, ssh, user, computer):
        usage = libtimekpr.get_usage(user, computer, ssh)
        return {"result": "success", "time_left": usage["time_left"], "time_spent": usage["time_spent"]}, 200
    else:
        return {"result": "fail"}, 500


@app.route("/decrease_time/<computer>/<user>/<seconds>")
def decrease_time(computer, user, seconds):
    """Decrease time limit for a user by specified seconds.

    Returns updated time_left and time_spent on success.
    """
    if validate_request(computer, user)["result"] == "fail":
        return validate_request(computer, user), 500
    ssh = libtimekpr.get_connection(computer)
    if libtimekpr.decrease_time(seconds, ssh, user, computer):
        usage = libtimekpr.get_usage(user, computer, ssh)
        return {"result": "success", "time_left": usage["time_left"], "time_spent": usage["time_spent"]}, 200
    else:
        return {"result": "fail"}, 500


@app.route("/increase_playtime/<computer>/<user>/<seconds>")
def increase_playtime(computer, user, seconds):
    """Increase playtime limit for a user by specified seconds.

    Returns updated playtime_left and playtime_spent on success.
    """
    if validate_request(computer, user)["result"] == "fail":
        return validate_request(computer, user), 500
    ssh = libtimekpr.get_connection(computer)
    if libtimekpr.increase_playtime(seconds, ssh, user, computer):
        usage = libtimekpr.get_usage(user, computer, ssh)
        return {"result": "success", "playtime_left": usage["playtime_left"], "playtime_spent": usage["playtime_spent"]}, 200
    else:
        return {"result": "fail"}, 500


@app.route("/decrease_playtime/<computer>/<user>/<seconds>")
def decrease_playtime(computer, user, seconds):
    """Decrease playtime limit for a user by specified seconds.

    Returns updated playtime_left and playtime_spent on success.
    """
    if validate_request(computer, user)["result"] == "fail":
        return validate_request(computer, user), 500
    ssh = libtimekpr.get_connection(computer)
    if libtimekpr.decrease_playtime(seconds, ssh, user, computer):
        usage = libtimekpr.get_usage(user, computer, ssh)
        return {"result": "success", "playtime_left": usage["playtime_left"], "playtime_spent": usage["playtime_spent"]}, 200
    else:
        return {"result": "fail"}, 500


@app.route("/favicon.ico")
def favicon():
    """Serve the favicon.ico file."""
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico", mimetype="image/vnd.microsoft.icon")


if __name__ == "__main__":
    """Run the Flask application directly."""
    app.run(host="0.0.0.0", port=8080)


def main():
    """Run the Flask application as poetry script entrypoint."""
    app.run(host="0.0.0.0", port=8080)
