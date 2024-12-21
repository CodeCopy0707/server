import os
import time
import logging
import threading
import datetime
import psutil
import telebot
from flask import Flask, send_from_directory
import schedule

# Initialize Flask app
app = Flask(__name__)

# Folder to store the HTML files
html_folder = './html_files/'

# Create folder if it doesn't exist
if not os.path.exists(html_folder):
    os.makedirs(html_folder)

# Admin chat ID (replace with your actual admin chat ID)
ADMIN_CHAT_ID = 7416312733  # Replace with your Telegram chat ID

# Initialize logs
log_file = 'server_logs.txt'
if not os.path.exists(log_file):
    with open(log_file, 'w') as log:
        log.write("Server logs initialized.\n")

# Start Flask app in a separate thread to run alongside the bot
def start_flask():
    app.run(host='0.0.0.0', port=5000)

# Function to serve the HTML file
@app.route('/<filename>')
def serve_html(filename):
    return send_from_directory(html_folder, filename)

# Function to convert file to HTML (Simple example for text files)
def convert_to_html(file_path):
    file_name = os.path.basename(file_path)
    html_file_path = os.path.join(html_folder, file_name.replace('.txt', '.html'))
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    with open(html_file_path, 'w') as f:
        f.write(f"<html><body><pre>{content}</pre></body></html>")
    
    return html_file_path

# Initialize the TeleBot with your bot token
TOKEN = '7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4'
bot = telebot.TeleBot(TOKEN)

# Function to handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome! Use /help to see available commands.")

# Function to handle /help command
@bot.message_handler(commands=['help'])
def help(message):
    commands = """
    /start - Start the bot and get a welcome message.
    /help - Get a list of available commands.
    /logs - Retrieve server logs.
    /uploadlog - Upload logs as a file.
    /clearlogs - Clear the server logs.
    /status - Check server status.
    /uptime - Check server uptime.
    /restart - Restart the bot and server.
    /listfiles - List all hosted files.
    /stopfile <filename> - Stop hosting a specific file.
    /remove <filename> - Remove a hosted file.
    /upload <file> - Upload a file to host as HTML.
    """
    bot.reply_to(message, commands)

# Function to handle /logs command
@bot.message_handler(commands=['logs'])
def logs(message):
    with open(log_file, 'r') as log:
        logs_content = log.read()
    bot.reply_to(message, logs_content)

# Function to handle /uploadlog command
@bot.message_handler(commands=['uploadlog'])
def uploadlog(message):
    with open(log_file, 'r') as log:
        bot.send_document(message.chat.id, log, caption="server_logs.txt")

# Function to handle /clearlogs command
@bot.message_handler(commands=['clearlogs'])
def clearlogs(message):
    if message.chat.id == ADMIN_CHAT_ID:
        with open(log_file, 'w') as log:
            log.write("Server logs cleared.\n")
        bot.reply_to(message, "Logs cleared successfully.")
    else:
        bot.reply_to(message, "You do not have permission to clear logs.")

# Function to handle /status command
@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, "Server is running.")

# Function to handle /uptime command
@bot.message_handler(commands=['uptime'])
def uptime(message):
    uptime = datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
    bot.reply_to(message, f"Server uptime: {str(uptime)}")

# Function to handle /restart command
@bot.message_handler(commands=['restart'])
def restart(message):
    if message.chat.id == ADMIN_CHAT_ID:
        bot.reply_to(message, "Restarting bot and server...")
        os._exit(0)  # Restart the bot
    else:
        bot.reply_to(message, "You do not have permission to restart the bot.")

# Function to handle /listfiles command
@bot.message_handler(commands=['listfiles'])
def listfiles(message):
    files = os.listdir(html_folder)
    if files:
        bot.reply_to(message, "\n".join(files))
    else:
        bot.reply_to(message, "No files are currently hosted.")

# Function to handle /stopfile command
@bot.message_handler(commands=['stopfile'])
def stopfile(message):
    if message.chat.id == ADMIN_CHAT_ID:
        filename = message.text.split(' ', 1)[1]
        if filename:
            file_path = os.path.join(html_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                bot.reply_to(message, f"File {filename} has been stopped from hosting.")
            else:
                bot.reply_to(message, f"File {filename} not found.")
        else:
            bot.reply_to(message, "Please specify a filename.")
    else:
        bot.reply_to(message, "You do not have permission to stop hosting files.")

# Function to handle /remove command
@bot.message_handler(commands=['remove'])
def remove(message):
    if message.chat.id == ADMIN_CHAT_ID:
        filename = message.text.split(' ', 1)[1]
        if filename:
            file_path = os.path.join(html_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                bot.reply_to(message, f"File {filename} has been removed.")
            else:
                bot.reply_to(message, f"File {filename} not found.")
        else:
            bot.reply_to(message, "Please specify a filename.")
    else:
        bot.reply_to(message, "You do not have permission to remove files.")

# Function to handle /upload command
@bot.message_handler(commands=['upload'])
def upload(message):
    if message.chat.id == ADMIN_CHAT_ID:
        if message.document:
            file = message.document
            file_path = f"./uploads/{file.file_name}"

            # Download the file
            file.download(file_path)

            # Convert the file to HTML
            if file.file_name.endswith('.txt'):
                html_file = convert_to_html(file_path)
                bot.reply_to(message, f"File uploaded and converted to HTML. You can access it at: http://<your-server-ip>:5000/{os.path.basename(html_file)}")
            else:
                bot.reply_to(message, "Only .txt files are supported for conversion to HTML.")
        else:
            bot.reply_to(message, "Please upload a file to host.")
    else:
        bot.reply_to(message, "You do not have permission to upload files.")

# Timer-based functionality to stop the server
def stop_server():
    schedule.every(24).hours.do(lambda: os._exit(0))  # Stops the bot after 24 hours (for example)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Main execution
if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start the Telegram bot in the main thread
    bot_thread = threading.Thread(target=bot.polling)
    bot_thread.daemon = True
    bot_thread.start()

    # Start timer to stop server
    timer_thread = threading.Thread(target=stop_server)
    timer_thread.daemon = True
    timer_thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(100)
