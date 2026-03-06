import os
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from supabase import create_client, Client

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# OpenAI 클라이언트 생성 (초기화?)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 채팅 요청 데이터 형식
class ChatRequest(BaseModel):
    message: str

# 채팅 API (POST)
@app.post("/chat")
def chat(request: ChatRequest):
    
    user_message = request.message

    # 사용자 메시지 저장
    supabase.table("messages").insert({
        "role": "user",
        "content": user_message
    }).execute()
    
    # ai 호출
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_message},
        ]
    )

    ai_message = response.choices[0].message.content

    # ai 메시지 저장
    supabase.table("messages").insert({
        "role": "assistant",
        "content": ai_message
    }).execute()

    return {
        "ai_message": ai_message
    }


# 채팅 기록 조회
@app.get("/messages")
def get_messages():

    response = supabase.table("messages") \
        .select("*") \
        .order("created_at") \
        .execute()
    
    return response.data

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