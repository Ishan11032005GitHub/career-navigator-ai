# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from graph import career_agent, learning_agent

load_dotenv()

app = FastAPI(title="Career Navigator AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Using LLM:", os.getenv("OLLAMA_MODEL", "llama3"))

@app.post("/api/career", response_model=ChatResponse)
def career(req: ChatRequest):
    result = career_agent(req.dict())
    return ChatResponse(reply=result.get("reply", ""))

@app.post("/api/learning", response_model=ChatResponse)
def learning(req: ChatRequest):
    result = learning_agent(req.dict())
    return ChatResponse(reply=result.get("reply", ""))

@app.get("/")
def root():
    return {"status": "ok", "service": "Career Navigator AI"}
