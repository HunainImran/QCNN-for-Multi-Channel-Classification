# Use the official Python 3.9 image
FROM python:3.9-slim

# Install system-level dependencies
RUN apt-get update && apt-get install -y\
    graphviz\
    gcc \
    build-essential \
    && apt-get clean

# Upgrade pip and install required Python packages
RUN pip install --upgrade pip
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Set the working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Default command to keep the container running (you can override this)
CMD ["bash"]
