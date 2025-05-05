# AUTOMATED CUSTOMER SUPPORT

It's a Telegram support bot using vector search that helps answer user questions, search the FAQ database using vector similarity, and translate the conversation to a human operator if necessary.

## Features

- Ask a question via Telegram
- Automatic answer from FAQ (vector search)
- Escalation to operator if no answer is found
- Operator can reply and add common questions to FAQ
- Logging of unanswered questions
- Admin command to update FAQ from logs

---

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Telegram Bot (python-telegram-bot)
- **Database**: Supabase 
- **Vector Search**: Vector embeddings 
- **Hosting**: Can run locally or deploy to any cloud (Render, Railway, etc.)

---

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/Boogyy/automated_customer_support
cd automated_customer_support
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

```bash
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
OPERATOR_GROUP_ID=your_telegram_operator_group_id
```

### 5. Run the project locally
#### Start FastAPI backend
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
#### Start the Telegram Bot
```bash
python3 bot.py
```


