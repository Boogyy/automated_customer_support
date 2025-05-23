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


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def handle_feedback_reject(call):
    """Handler for user rejection of a response"""
    user_id = int(call.data.split("_")[1])

    if user_id not in pending_questions:
        bot.send_message(user_id, "Your question was not found pending. Please try again later.")
        return

    # Remove the buttons to prevent the user from pressing them again
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    bot.send_message(user_id, "We have resent your question to the operator. Please expect a new reply.")
    bot.send_message(OPERATOR_GROUP_ID, f"User {user_id} not satisfied with the answer. A new answer is required.\n"
                                        f"Question: {pending_questions[user_id]['question']}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def handle_feedback_accept(call):
    """User response acceptance handler"""
    user_id = int(call.data.split("_")[1])

    if user_id not in pending_questions:
        bot.send_message(user_id, "Your question was not found pending. Please try again later.")
        return

    # Remove the buttons to prevent the user from pressing them again
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # Taking a question off the waiting list
    del pending_questions[user_id]
    bot.send_message(user_id, "✅ Thank you for the confirmation! Your issue has been resolved.")
    bot.send_message(OPERATOR_GROUP_ID, f"✅ The reply was accepted by the user {user_id}. Question resolved.")



@bot.message_handler(commands=["add_faq"])
def handle_add_faq(message):
    """Handler of the /add_faq <ID> command"""
    if message.chat.id != OPERATOR_GROUP_ID:
        bot.send_message(message.chat.id, "❌ This command is only available to the operator.")
        return

    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(OPERATOR_GROUP_ID, "⚠️ Use the format: /add_faq <ID of question>")
        return

    question_id = int(parts[1])

    try:
        response = requests.post(ADD_FAQ_URL, json={"question_id": question_id})

        if response.status_code == 200:
            bot.send_message(OPERATOR_GROUP_ID, response.json()["message"])
        else:
            bot.send_message(OPERATOR_GROUP_ID, "Error when adding to FAQ.")
    except Exception as e:
        bot.send_message(OPERATOR_GROUP_ID, f"❌ Failed to add to FAQ: {e}")


bot.polling(none_stop=True)