import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/process_question")
ANSWER_URL = os.getenv("ANSWER_URL", "http://127.0.0.1:8000/process_answer")
ADD_FAQ_URL = os.getenv("ADD_FAQ_URL", "http://127.0.0.1:8000/add_to_faq")
OPERATOR_GROUP_ID = int(os.getenv("OPERATOR_GROUP_ID", "-1002626409614"))

bot = telebot.TeleBot(TOKEN)
pending_questions = {}  # user_id -> {"message_id": ID, "question": TEXT, "reply_message_id": ID}


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Good afternoon, this is an automated support bot!\n "
                                      "You can ask your question and we will try to answer it!\n "
                                      "If necessary, we will send the question to the operator.")
    

@bot.message_handler(func=lambda message: message.chat.id != OPERATOR_GROUP_ID)
def handle_user_message(message):
    """Handling messages from users"""
    user_id = message.chat.id
    text = message.text

    response = requests.post(API_URL, json={"user_id": user_id, "question": text})

    if response.status_code != 200:
        bot.send_message(user_id, "There's been an error. Try again later.")
        return

    try:
        data = response.json()

        if "answer" in data:
            bot.send_message(user_id, data["answer"])
        elif "message" in data and data["message"] == "Sent to operator":
            bot.send_message(user_id, "Your question has been sent to the operator. Please wait for a reply.")
            pending_questions[user_id] = {"message_id": message.message_id, "question": text, "reply_message_id": None}
        else:
            bot.send_message(user_id, "Error: unexpected response from API")
    except requests.exceptions.JSONDecodeError:
        bot.send_message(user_id, "Data processing error. Try again later.")


@bot.message_handler(func=lambda message: message.chat.id == OPERATOR_GROUP_ID and " " in message.text and not message.text.startswith("/"))
def handle_operator_response(message):
    """Handling operator responses"""
    parts = message.text.split(" ", 1)

    try:
        user_id = int(parts[0])
        answer = parts[1]

        if user_id not in pending_questions:
            bot.send_message(OPERATOR_GROUP_ID, "Error: No question from this user is pending.")
            return

        question_text = pending_questions[user_id]["question"]

        # Sending a response to the API
        response = requests.post(ANSWER_URL, json={"user_id": user_id, "answer": answer, "question": question_text})

        if response.status_code == 200:
            # Sending a reply to the user
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ The answer is apt", callback_data=f"accept_{user_id}"),
                InlineKeyboardButton("❌ The answer doesn't fit", callback_data=f"reject_{user_id}")
            )

            bot.send_message(user_id, f"✅ Operator's reply:\n{answer}", reply_markup=markup)
            bot.send_message(OPERATOR_GROUP_ID, "✅ Reply sent to user.")
        else:
            bot.send_message(OPERATOR_GROUP_ID, "Error when saving a reply.")
    except (IndexError, ValueError, KeyError):
        bot.send_message(OPERATOR_GROUP_ID, "Error: use the format '<user_id> <reply>'.")


@bot.message_handler(func=lambda message: message.chat.id == OPERATOR_GROUP_ID and not message.text.startswith("/") and " " not in message.text)
def handle_unstructured_operator_message(message):
    """Processes operator messages if they do not conform to the format <user_id> <reply>"""
    bot.send_message(OPERATOR_GROUP_ID, "Error: use the format '<user_id> <reply>' to reply to a user.")


bot.polling(none_stop=True)