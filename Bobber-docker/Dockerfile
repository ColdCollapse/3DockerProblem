# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv for managing Python dependencies
RUN pip install pipenv

# Clone the Bobber repository
RUN git clone https://github.com/Flangvik/Bobber.git .

# Install dependencies from Pipfile (if Pipfile exists)
RUN pipenv install --deploy --ignore-pipfile

# Expose any necessary ports (customize based on Bobber's requirements)
EXPOSE 8080

# Set the entrypoint or command to run the Bobber tool (modify according to its usage)
CMD ["pipenv", "run", "python", "bobber.py"]
