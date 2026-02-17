import os
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"message": "Server is running! Let's chat!"}

@app.get("/chat-test")
def chat_test():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "안녕! 즐거운 명절 보내고 있니?"},
        ]
    )
    return {"response": response.choices[0].message.content}