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
    user_id = message.chat.id
    text = message.text

    response = requests.post(API_URL, json={"user_id": user_id, "question": text})
    data = response.json()

    if "answer" in data:
        bot.send_message(user_id, data["answer"])
    else:
        bot.send_message(user_id, "Your question has been sent to an operator.")


@bot.message_handler(func=lambda m: m.chat.id == OPERATOR_GROUP_ID and " " in m.text)
def handle_operator_response(message):
    try:
        user_id, answer = message.text.split(" ", 1)
        user_id = int(user_id)

        # send to API
        requests.post(ANSWER_URL, json={
            "user_id": user_id,
            "question": "Unknown",  # without question by the moment
            "answer": answer
        })

        bot.send_message(user_id, f"✅ Operator's answer:\n{answer}")
    except Exception:
        bot.send_message(OPERATOR_GROUP_ID, "⚠️ Use: <user_id> <answer>")


@bot.message_handler(func=lambda message: message.chat.id == OPERATOR_GROUP_ID and not message.text.startswith("/") and " " not in message.text)
def handle_unstructured_operator_message(message):
    """Processes operator messages if they do not conform to the format <user_id> <reply>"""
    bot.send_message(OPERATOR_GROUP_ID, "Error: use the format '<user_id> <reply>' to reply to a user.")


bot.polling(none_stop=True)