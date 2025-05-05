import uvicorn
from fastapi import FastAPI
import telebot
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "API is working!"}


# establish Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Initialization sentence-transformers
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPERATOR_GROUP_ID = int(os.getenv("OPERATOR_GROUP_ID", "-1002626409614"))
bot = telebot.TeleBot(BOT_TOKEN)


def get_embedding(text: str):
    """Generating a question vector using sentence-transformers"""
    return model.encode(text).tolist()


class QuestionAnswerUpdate(BaseModel):
    question_id: int
    new_answer: str


@app.post("/process_question")
async def process_question(data: dict):
    user_id = data["user_id"]
    question = data["question"]

    # Question vector generation
    question_vector = get_embedding(question)

    # Search in faq_vectors
    response_faq = supabase.rpc("match_faq",
                                {"query_embedding": question_vector, "match_threshold": 0.9, "match_count": 1}).execute()

    if response_faq.data:
        best_match = response_faq.data[0]
        return {"answer": best_match["answer"]}

    # Search in question_logs
    response_logs = supabase.rpc("match_question_logs",
                                 {"query_embedding": question_vector, "match_threshold": 0.75, "match_count": 1}).execute()

    if response_logs.data:
        best_match = response_logs.data[0]
        question_id = best_match["id"]
        current_count = best_match["count"]
        new_count = current_count + 1

        # Update the quantity for the question found
        supabase.table("question_logs").update({
            "count": new_count
        }).eq("id", question_id).execute()

        # Send it to the operator that it's a similar question
        bot.send_message(OPERATOR_GROUP_ID, f"🔔 Related question from {user_id}:\n"
                                      f"❓ {best_match['question']}\n"
                                      f"📌 Answer: {best_match['answer']}\n"
                                      f"🔥 Asked {new_count} time(s)\n"
                                      f"🔥 Id to add: {question_id}\n"
                                      f"✍️ New question: {question}")
    else:
        bot.send_message(OPERATOR_GROUP_ID, f"🔔 A new question from {user_id}:\n❓ {question}\n"
                                            f"Reply in the format <user_id> answer")

    return {"message": "Sent to operator"}


@app.post("/process_answer")
async def process_answer(data: dict):
    """The operator answers the question, and it is stored in Supabase"""
    user_id = data["user_id"]
    question = data["question"]
    answer = data["answer"]

    # Generating a question vector
    question_vector = get_embedding(question)

    # 🔹 Check if the question already exists in question_logs
    response_logs = supabase.rpc("match_question_logs",
                                 {"query_embedding": question_vector, "match_threshold": 0.75, "match_count": 1}).execute()

    if response_logs.data:
        # If there is a similar question → update it
        best_match = response_logs.data[0]
        supabase.table("question_logs").update({
            "answer": answer,
            "count": best_match["count"] + 1
        }).eq("id", best_match["id"]).execute()
    else:
        # If the question is new → add to question_logs
        supabase.table("question_logs").insert({
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "embedding": question_vector,
            "count": 1
        }).execute()

    bot.send_message(OPERATOR_GROUP_ID, f"✅ Answer saved:\n❓ {question}\n📌 {answer}")
    return {"message": "Answer saved"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)