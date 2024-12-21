import telebot
import google.generativeai as genai

# Telegram and Gemini API keys
TELEGRAM_TOKEN = "7333847070:AAFUwJpWNvTZTQLVIsbcCicJZlWAmqFFNa4"
GEMINI_API_KEY = "AIzaSyCWFRHQ3B9A-wERY9QbggKWHffLeHkAuzg"

# Initialize the Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Configure Google Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to generate a more explicit adult response in Hinglish
def generate_adult_response(user_input):
    try:
        response = model.generate_content(f"Respond ethical hacking teacher and programmer in Hinglish. The user said: {user_input}")
        return response.text.strip()
    except Exception as e:
        return f"Sorry baby, I can't fulfill that request right now. 😘"

# Start Command: Start conversation with the bot
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Hi there!😊")

# Default Message Handler: Respond to user input with adult Hinglish response
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    response = generate_adult_response(user_input)
    bot.reply_to(message, response)

# Run the bot
if __name__ == "__main__":
    bot.polling()
