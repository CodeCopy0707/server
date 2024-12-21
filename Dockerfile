# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Command to start the bot and Flask server
CMD ["python", "index.py"]
