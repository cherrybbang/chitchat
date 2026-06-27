# Chitchat

AI 기반 실시간 채팅 백엔드 API입니다. FastAPI와 OpenAI를 사용하며, Supabase로 사용자 인증 및 메시지를 저장합니다.

## 주요 기능

- Bearer 토큰 기반 사용자 인증 (Supabase Auth)
- 룸(room) 단위 채팅 — 대화 맥락 최근 20개 메시지 유지
- OpenAI GPT-4o-mini를 활용한 AI 응답 생성
- 메시지 저장 및 삭제

## 기술 스택

| 분류 | 기술 |
|------|------|
| Framework | FastAPI |
| AI | OpenAI GPT-4o-mini |
| 데이터베이스 | Supabase (PostgreSQL) |
| 인증 | Supabase Auth + HTTP Bearer |
| 서버 | Uvicorn (ASGI) |

## 시작하기

### 요구사항

- Python 3.10 이상
- Supabase 프로젝트
- OpenAI API 키

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd chitchat

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 의존성 설치
pip install -r requirements.txt
```

### 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고 아래 값을 채웁니다.

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=<service-role-key>
ALLOWED_ORIGINS=http://localhost:5173
```

> `ALLOWED_ORIGINS`에 여러 출처를 허용할 경우 쉼표로 구분합니다.  
> e.g. `http://localhost:5173,https://example.com`

### 실행

```bash
uvicorn main:app --reload
# http://localhost:8000
```

## API

모든 엔드포인트는 `Authorization: Bearer <token>` 헤더가 필요합니다.

### POST /chat

메시지를 전송하고 AI 응답을 받습니다.

**Request body**
```json
{
  "message": "안녕하세요",
  "room_id": "room-uuid"
}
```

**Response**
```json
{
  "ai_message": "안녕하세요! 무엇을 도와드릴까요?"
}
```

### DELETE /messages/{message_id}

특정 메시지를 삭제합니다.

**Response**
```json
{
  "message": "deleted"
}
```

## 데이터베이스 스키마

Supabase에서 아래 테이블을 생성해야 합니다.

```sql
create table messages (
  id          uuid primary key default gen_random_uuid(),
  room_id     text not null,
  role        text not null check (role in ('user', 'bot')),
  content     text not null,
  created_at  timestamptz default now()
);
```

## 프로젝트 구조

```
chitchat/
├── main.py           # API 라우터, 인증, 비즈니스 로직
├── requirements.txt  # 의존성 목록
└── .env              # 환경 변수 (git 추적 제외)
```
