import os
import telebot
import logging
from flask import Flask, send_from_directory
from threading import Thread
from datetime import datetime, timedelta
import subprocess
import time

# Telegram Bot Configuration
ADMIN_CHAT_ID = "7416312733"  # Replace with your Telegram chat ID
bot = telebot.TeleBot('7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4')

# Flask App Configuration
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)

# Logs Configuration
log_file = "server_logs.txt"
logging.basicConfig(level=logging.INFO, filename=log_file, filemode="w")

# Global Variables
active_hosted_files = {}
public_url = None
start_time = datetime.now()

# Flask Routes
@app.route("/")
def index():
    return "🤖 Welcome to the Hosting Bot Server!"

@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Function to start Localtunnel and get the public URL
def start_localtunnel():
    global public_url
    try:
        port = int(os.getenv("PORT", 5000))  # Use dynamic port binding
        result = subprocess.Popen(['lt', '--port', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in iter(result.stdout.readline, b""):
            if b"your url is" in line:
                public_url = line.decode().strip().split()[-1]
                print(f"🌍 Localtunnel URL: {public_url}")
                break
        else:
            print("🚫 Localtunnel failed to start.")
    except Exception as e:
        print(f"❌ Error with Localtunnel: {e}")

# Telegram Bot Handlers (Admin Commands)
@bot.message_handler(commands=["start"])
def send_welcome(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    bot.reply_to(
        message,
        "👋 Welcome to the Advanced HTML Hosting Bot!\n\n"
        "📂 Upload an HTML file to host it.\n"
        "🛠 Use `/help` to see all available commands.",
    )

@bot.message_handler(commands=["help"])
def send_help(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    help_text = """
📖 **Admin Commands**:
1. **/start** - Start the bot and get a welcome message.
2. **/help** - Get a list of available commands.
3. **/logs** - Retrieve server logs.
4. **/uploadlog** - Upload logs as a file.
5. **/clearlogs** - Clear the server logs.
6. **/status** - Check server status.
7. **/uptime** - Check server uptime.
8. **/restart** - Restart the bot and server.
9. **/listfiles** - List all hosted files.
10. **/stopfile <filename>** - Stop hosting a specific file.
11. **/remove <filename>** - Remove a hosted file.
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=["logs"])
def send_logs(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    if os.path.exists(log_file):
        with open(log_file, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.reply_to(message, "🚫 No logs found.")

@bot.message_handler(commands=["uploadlog"])
def upload_log_file(message):
    if os.path.exists(log_file):
        with open(log_file, "rb") as f:
            bot.send_document(message.chat.id, f, caption="📜 Server Logs")
    else:
        bot.reply_to(message, "🚫 No logs to upload.")

@bot.message_handler(commands=["clearlogs"])
def clear_logs(message):
    global log_file
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    with open(log_file, "w") as f:
        f.truncate(0)  # Clear log file
    bot.reply_to(message, "🧹 Server logs cleared.")

@bot.message_handler(commands=["uptime"])
def send_uptime(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    uptime = datetime.now() - start_time
    bot.reply_to(message, f"⏱ Uptime: {str(uptime).split('.')[0]}")

@bot.message_handler(commands=["restart"])
def restart_bot(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    bot.reply_to(message, "🔄 Restarting bot...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.message_handler(commands=["status"])
def send_status(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    status_text = "✅ The server is running and ready to host files."
    if active_hosted_files:
        status_text += f"\n📂 Active hosted files: {len(active_hosted_files)}"
    if public_url:
        status_text += f"\n🌐 Public URL: {public_url}"
    bot.reply_to(message, status_text)

@bot.message_handler(commands=["listfiles"])
def list_files(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        bot.reply_to(message, "🚫 Access denied! Only the admin can use this bot.")
        return
    if active_hosted_files:
        file_list = "\n".join([f"{name} - {url}" for name, url in active_hosted_files.items()])
        bot.reply_to(message, f"📂 Hosted Files:\n{file_list}")
    else:
        bot.reply_to(message, "🚫 No files are currently hosted.")

@bot.message_handler(commands=["stopfile"])
def stop_file(message):
    try:
        _, filename = message.text.split(" ", 1)
        if filename in active_hosted_files:
            del active_hosted_files[filename]
            bot.reply_to(message, f"✅ File `{filename}` stopped successfully from hosting.")
        else:
            bot.reply_to(message, "🚫 File not found in the active hosted list.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error stopping file: {e}")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        file_extension = message.document.file_name.split(".")[-1].lower()
        if file_extension != "html":
            bot.reply_to(message, "🚫 Only HTML files are allowed!")
            return
        file_path = os.path.join(UPLOAD_FOLDER, message.document.file_name)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, "wb") as f:
            f.write(downloaded_file)
        bot.reply_to(message, f"✅ File `{message.document.file_name}` uploaded successfully! Hosting it now...")
        global public_url
        if not public_url:
            start_localtunnel()
        file_url = f"{public_url}/{message.document.file_name}"
        active_hosted_files[message.document.file_name] = file_url
        bot.reply_to(message, f"🌐 Your file is hosted at: {file_url}")
        Thread(target=app.run, kwargs={"port": int(os.getenv("PORT", 5000))}).start()
    except Exception as e:
        bot.reply_to(message, f"❌ Error processing your file: {e}")

# Start the bot
def start_bot():
    print("🤖 Bot is running...")
    bot.infinity_polling()

# Run the bot and server together
if __name__ == "__main__":
    Thread(target=start_bot).start()
