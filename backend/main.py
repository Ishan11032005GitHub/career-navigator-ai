# main.py
import os
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse
from graph import app_graph

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

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    state: Dict[str, Any] = {
        "message": req.message,
        "resume_text": req.resume_text or "",
        "job_posts": req.job_posts or [],
    }
    result = app_graph.invoke(state, config={"configurable": {"thread_id": req.thread_id}})
    return ChatResponse(reply=result.get("reply", ""), audio_b64=result.get("audio_b64"))


@app.get("/")
def root():
    return {"status": "ok", "service": "Career Navigator AI (Ollama mode)"}
