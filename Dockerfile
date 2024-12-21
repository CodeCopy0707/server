# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Install Node.js and npm (required for LocalTunnel)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Set the working directory inside the container
WORKDIR /app

# Copy the local requirements.txt to the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install LocalTunnel globally
RUN npm install -g localtunnel

# Copy the rest of the application files to the container
COPY . /app/

# Expose the Flask app port (5000)
EXPOSE 5000

# Command to start the Flask server and localtunnel (without subdomain)
CMD ["sh", "-c", "python index.py & lt --port 5000"]
