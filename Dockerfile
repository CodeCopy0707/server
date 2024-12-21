# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install Node.js (required for localtunnel) and curl to fetch Node.js setup script
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install localtunnel globally
RUN npm install -g localtunnel

# Copy the project files into the container
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Command to start the Flask server and localtunnel (without subdomain)
CMD ["sh", "-c", "python index.py & lt --port 5000"]
