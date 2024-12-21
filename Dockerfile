# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the local requirements.txt to the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the container
COPY . /app/

# Expose the Flask app port
EXPOSE 5000

# Run the Flask app and the Telegram bot

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Command to start the Flask server and localtunnel (without subdomain)
CMD ["sh", "-c", "python index.py & lt --port 5000"]
