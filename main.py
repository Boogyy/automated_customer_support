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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)