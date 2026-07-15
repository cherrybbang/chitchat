import os
import time
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from supabase import create_client, Client

load_dotenv()

# /docs 문서 노출 방지
app = FastAPI(docs_url=None, redoc_url=None)

origins = os.getenv("ALLOWED_ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# 토큰 검증 함수 추가
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        result = supabase.auth.get_user(credentials.credentials)
        if not result.user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return result.user
    except Exception as e:
        print("AUTH ERROR:", e)
        raise HTTPException(status_code=401, detail="Unauthorized")

# Rate limiting 설정 - 사용자 한 명이 무한정 OpenAI를 호출하지 못하도록 제한
RATE_LIMIT_PER_MINUTE = 2   # 분당 최대 호출 수 (폭주/무한루프 차단)
RATE_LIMIT_PER_DAY = 300     # 하루 최대 호출 수 (비용 안전망)

# 사용자별 호출 시각 기록. {user_id: [timestamp, ...]}
# 메모리에 저장하므로 서버 재시작 시 초기화됨 (단일 인스턴스 기준으로 충분)
user_call_history = defaultdict(list)

def check_rate_limit(current_user=Depends(get_current_user)):
    now = time.time()
    user_id = current_user.id

    # 하루(86400초)보다 오래된 기록은 버리고 유지
    history = [ts for ts in user_call_history[user_id] if now - ts < 86400]

    calls_last_minute = sum(1 for ts in history if now - ts < 60)
    calls_last_day = len(history)

    if calls_last_minute >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="요청이 너무 잦습니다. 잠시 후 다시 시도해주세요.")
    if calls_last_day >= RATE_LIMIT_PER_DAY:
        raise HTTPException(status_code=429, detail="하루 호출 한도를 초과했습니다. 내일 다시 시도해주세요.")

    # 이번 호출을 기록
    history.append(now)
    user_call_history[user_id] = history

    return current_user

class ChatRequest(BaseModel):
    message: str = Field(max_length=1000)
    room_id: str

@app.post("/chat")
def chat(request: ChatRequest, current_user=Depends(check_rate_limit)):
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


# 전체 메시지를 가져오는 엔드포인트. 
# room_id 필터없이 모든 유저의 메시지가 노출되는 이슈로 주석처리함.
# @app.get("/messages")
# def get_messages(current_user=Depends(get_current_user)):
#     response = supabase.table("messages") \
#         .select("*") \
#         .order("created_at") \
#         .execute()

#     return response.data


@app.delete("/messages/{message_id}")
def delete_message(message_id: str, current_user=Depends(get_current_user)):
    supabase.table("messages") \
        .delete() \
        .eq("id", message_id) \
        .execute()

    return {"message": "deleted"}


# 테스트용 엔드포인트.
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