FROM python:3.12-slim

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /app

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create a virtual environment in Docker
RUN poetry config virtualenvs.create false

# Install only production dependencies (without the project itself)
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Copy the rest of the application
COPY timekpr ./timekpr
COPY templates ./templates
COPY static ./static
COPY conf.example.yaml ./conf.yaml

# Now install the project itself
RUN poetry install --only main --no-interaction --no-ansi

# Run the application using the poetry script entrypoint
CMD ["timekpr-next-web"]
