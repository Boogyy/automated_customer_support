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
    

bot.polling(none_stop=True)