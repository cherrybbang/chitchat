import os
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# OpenAI 클라이언트 생성 (초기화?)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 채팅 요청 데이터 형식
class ChatRequest(BaseModel):
    message: str

# 채팅 API (POST)
@app.post("/chat")
def chat(request: ChatRequest):
    
    user_message = request.message
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_message},
        ]
    )

    ai_message = response.choices[0].message.content

    return {
        "user_message": user_message,
        "ai_message": ai_message
    }

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