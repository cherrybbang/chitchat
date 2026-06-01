import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class ChatRequest(BaseModel):
    message: str = Field(max_length=1000)
    room_id: str

@app.post("/chat")
def chat(request: ChatRequest):
    supabase.table("messages").insert({
        "room_id": request.room_id,
        "role": "user",
        "content": request.message
    }).execute()

    history = supabase.table("messages") \
        .select("*") \
        .eq("room_id", request.room_id) \
        .order("created_at") \
        .execute()

    recent = history.data[-20:]
    messages = [
        {"role": "assistant" if msg["role"] == "bot" else "user", "content": msg["content"]}
        for msg in recent
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=500
    )

    ai_message = response.choices[0].message.content

    supabase.table("messages").insert({
        "room_id": request.room_id,
        "role": "bot",
        "content": ai_message
    }).execute()

    return {"ai_message": ai_message}


@app.get("/messages")
def get_messages():
    response = supabase.table("messages") \
        .select("*") \
        .order("created_at") \
        .execute()

    return response.data


@app.delete("/messages/{message_id}")
def delete_message(message_id: str):
    supabase.table("messages") \
        .delete() \
        .eq("id", message_id) \
        .execute()

    return {"message": "deleted"}


# @app.get("/")
# def root():
#     return {"message": "Server is running! Let's chat!"}

# @app.get("/chat-test")
# def chat_test():
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "안녕! 즐거운 명절 보내고 있니?"},
#         ]
#     )
#     return {"response": response.choices[0].message.content}