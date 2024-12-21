import asyncio
import websockets
import json
import os
import telebot
from datetime import datetime
from collections import deque

# Telegram Bot Configuration
API_TOKEN = "YOUR_TELEGRAM_BOT_API_TOKEN"  # Replace with your Telegram bot API token
CHAT_ID = "YOUR_CHAT_ID"  # Replace with your Telegram chat ID
bot = telebot.TeleBot(API_TOKEN)

# Log file path
LOG_FILE = "logs/logs.txt"
clients = set()  # Active WebSocket clients
command_history = deque(maxlen=100)  # Keeps last 100 commands

# Authentication
VALID_TOKENS = {"your_valid_token_here"}  # List of valid tokens for client authentication

# --- File Handling ---
# Save data to a file
def save_to_file(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # Create directory if it doesn't exist
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
    bot.send_message(message.chat.id, "Hello! I am your advanced server bot. Use /getlogs to view logs, /getclients to see active clients, and /sendmessage to communicate with clients.")

# Get logs
@bot.message_handler(commands=['getlogs'])
def get_logs(message):
    logs = read_file(LOG_FILE)
    bot.send_message(message.chat.id, f"📜 Logs:\n{logs}")

# Get active clients
@bot.message_handler(commands=['getclients'])
def get_clients(message):
    if clients:
        client_list = "\n".join([str(client.remote_address) for client in clients])
        bot.send_message(message.chat.id, f"🟢 Active Clients:\n{client_list}")
    else:
        bot.send_message(message.chat.id, "❌ No active clients connected.")

# Send a message to a specific client
@bot.message_handler(commands=['sendmessage'])
def send_message_to_client(message):
    try:
        # Example format: /sendmessage client_address your_message_here
        parts = message.text.split(" ", 2)
        client_address = parts[1]
        msg_content = parts[2]
        
        for client in clients:
            if str(client.remote_address) == client_address:
                asyncio.run(client.send(json.dumps({"command": "message", "result": msg_content, "timestamp": str(datetime.now())})))
                bot.send_message(message.chat.id, f"✅ Message sent to client {client_address}")
                return

        bot.send_message(message.chat.id, f"❌ No client found with address {client_address}")
    except IndexError:
        bot.send_message(message.chat.id, "❌ Invalid command format. Use /sendmessage client_address your_message_here")

# Restart the server
@bot.message_handler(commands=['restart'])
def restart_server(message):
    bot.send_message(message.chat.id, "🔄 Restarting the server...")
    os.execv(sys.executable, ['python'] + sys.argv)  # Restart the application

# Send a message to Telegram
def send_to_telegram(data):
    bot.send_message(CHAT_ID, f"🔔 New Update: {data}")

# Run Telegram Bot
def run_bot():
    print("Telegram Bot started...")
    bot.polling()

# --- WebSocket Server ---
async def handler(websocket, path):
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    send_to_telegram(f"🟢 New client connected: {websocket.remote_address}")

    # Authentication Process
    try:
        # Send a message to authenticate
        await websocket.send(json.dumps({"command": "auth", "result": "Please authenticate with your token."}))
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)

        if auth_data.get("command") == "auth" and auth_data.get("result") in VALID_TOKENS:
            # Authentication successful
            await websocket.send(json.dumps({"command": "auth", "result": "Authentication successful."}))
            print(f"Client {websocket.remote_address} authenticated successfully.")
            send_to_telegram(f"🟢 Client {websocket.remote_address} authenticated successfully.")
        else:
            # Authentication failed
            await websocket.send(json.dumps({"command": "auth", "result": "Authentication failed."}))
            print(f"Client {websocket.remote_address} failed to authenticate.")
            send_to_telegram(f"❌ Client {websocket.remote_address} failed authentication.")
            return

        async for message in websocket:
            data = json.loads(message)  # Parse JSON message
            formatted_data = f"Command: {data['command']}, Result: {data['result']}, Timestamp: {data['timestamp']}"
            print(f"Received: {formatted_data}")

            # Save to log file
            save_to_file(LOG_FILE, formatted_data)

            # Notify Telegram about new data
            send_to_telegram(f"📩 New data received:\n{formatted_data}")

            # Add to command history
            command_history.append(formatted_data)

            # Forward the message to all connected clients (C2C communication)
            for client in clients:
                if client != websocket:
                    await client.send(json.dumps(data))
    except Exception as e:
        print(f"Error with client {websocket.remote_address}: {e}")
        send_to_telegram(f"❌ Error with client {websocket.remote_address}: {e}")
    finally:
        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")
        send_to_telegram(f"❌ Client disconnected: {websocket.remote_address}")

# Start WebSocket server
async def start_server():
    # Fetch the port from the environment variable
    port = int(os.getenv("PORT", 10000))  # Default to 10000 if the environment variable is not set
    
    print(f"WebSocket Server started on ws://0.0.0.0:{port}")
    server = await websockets.serve(handler, "0.0.0.0", port)
    await server.wait_closed()

# Run everything together
if __name__ == "__main__":
    # Run Telegram bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start WebSocket server
    asyncio.run(start_server())
