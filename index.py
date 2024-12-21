

import os
import time
import logging
from flask import Flask, send_from_directory
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading
import schedule
import psutil
import datetime

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

# Start the bot
def start_bot(token):
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    
    def start(update, context):
        update.message.reply_text("Welcome! Use /help to see available commands.")
    
    def help(update, context):
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
        """
        update.message.reply_text(commands)

    def logs(update, context):
        with open(log_file, 'r') as log:
            logs = log.read()
        update.message.reply_text(logs)

    def uploadlog(update, context):
        with open(log_file, 'r') as log:
            update.message.reply_document(document=log, filename="server_logs.txt")
    
    def clearlogs(update, context):
        if update.message.chat_id == ADMIN_CHAT_ID:
            with open(log_file, 'w') as log:
                log.write("Server logs cleared.\n")
            update.message.reply_text("Logs cleared successfully.")
        else:
            update.message.reply_text("You do not have permission to clear logs.")
    
    def status(update, context):
        status_message = "Server is running."
        update.message.reply_text(status_message)
    
    def uptime(update, context):
        uptime = datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
        update.message.reply_text(f"Server uptime: {str(uptime)}")
    
    def restart(update, context):
        if update.message.chat_id == ADMIN_CHAT_ID:
            update.message.reply_text("Restarting bot and server...")
            os._exit(0)  # Restart the bot (ends the process, which restarts the bot)
        else:
            update.message.reply_text("You do not have permission to restart the bot.")
    
    def listfiles(update, context):
        files = os.listdir(html_folder)
        if files:
            update.message.reply_text("\n".join(files))
        else:
            update.message.reply_text("No files are currently hosted.")

    def stopfile(update, context):
        if update.message.chat_id == ADMIN_CHAT_ID:
            filename = " ".join(context.args)
            if filename:
                file_path = os.path.join(html_folder, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    update.message.reply_text(f"File {filename} has been stopped from hosting.")
                else:
                    update.message.reply_text(f"File {filename} not found.")
            else:
                update.message.reply_text("Please specify a filename.")
        else:
            update.message.reply_text("You do not have permission to stop hosting files.")
    
    def remove(update, context):
        if update.message.chat_id == ADMIN_CHAT_ID:
            filename = " ".join(context.args)
            if filename:
                file_path = os.path.join(html_folder, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    update.message.reply_text(f"File {filename} has been removed.")
                else:
                    update.message.reply_text(f"File {filename} not found.")
            else:
                update.message.reply_text("Please specify a filename.")
        else:
            update.message.reply_text("You do not have permission to remove files.")
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('logs', logs))
    dispatcher.add_handler(CommandHandler('uploadlog', uploadlog))
    dispatcher.add_handler(CommandHandler('clearlogs', clearlogs))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('uptime', uptime))
    dispatcher.add_handler(CommandHandler('restart', restart))
    dispatcher.add_handler(CommandHandler('listfiles', listfiles))
    dispatcher.add_handler(CommandHandler('stopfile', stopfile))
    dispatcher.add_handler(CommandHandler('remove', remove))

    updater.start_polling()

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

    # Telegram Bot Token (replace with your actual bot token)
    token = '7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4'
    
    # Start Telegram bot in the main thread
    bot_thread = threading.Thread(target=start_bot, args=(token,))
    bot_thread.daemon = True
    bot_thread.start()

    # Start timer to stop server
    timer_thread = threading.Thread(target=stop_server)
    timer_thread.daemon = True
    timer_thread.start()

    # Keep the main thread alive
    while True:
        time.sleep(100)
