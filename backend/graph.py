import os, sys, base64, requests, json
from dotenv import load_dotenv
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from tools import analyze_resume, match_jobs, generate_learning_path, quick_quiz

# --- Load env file early ---
if not load_dotenv():
    print("⚠️ Warning: .env file not found", file=sys.stderr)

# Ollama config (free local LLM)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ---- Ollama invoke ----
def safe_llm_invoke(prompt: str) -> str:
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt},
            stream=True,
            timeout=60
        )
        text = ""
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        text += data["response"]
                except Exception:
                    continue
        return text.strip() or "⚠️ Ollama returned no output."
    except Exception as e:
        return f"⚠️ Ollama error: {str(e)}"

# ---- Fake TTS (silence) ----
def synthesize_audio(text: str) -> str:
    return base64.b64encode(b"\x00" * 1024).decode("utf-8")

# ---- Agent nodes ----
def router(state: Dict[str, Any]):
    text = (state.get("message") or "").lower()
    intent = "chat"
    if any(k in text for k in ["job", "resume", "apply", "hiring", "jd", "role"]):
        intent = "career"
    if any(k in text for k in ["learn", "teach", "quiz", "study", "course", "path"]):
        intent = "learning"
    return {"intent": intent}

def career_agent(state: Dict[str, Any]):
    resume_text = state.get("resume_text") or ""
    job_posts = state.get("job_posts") or []
    analysis = analyze_resume(resume_text) if resume_text else {"skills": [], "suggestions": []}
    ranked = match_jobs(analysis["skills"], job_posts) if job_posts else []
    prompt = (
        "You are a concise career coach. Based on the skills and suggestions, write a short reply.\n"
        f"User message: {state.get('message')}\n"
        f"Detected skills: {analysis['skills']}\n"
        f"Suggestions: {analysis['suggestions']}\n"
        f"Top job match titles: {[p.get('title') for p in ranked[:3]]}\n"
    )
    return {"reply": safe_llm_invoke(prompt)}

def learning_agent(state: Dict[str, Any]):
    topic = state.get("message", "a topic")
    path = generate_learning_path(topic)
    quiz = quick_quiz(topic)
    prompt = (
        "You are a crisp learning mentor. Respond with: "
        "1) mini roadmap 2) two quiz questions 3) one tiny project idea.\n"
        f"Topic: {topic}\n"
        f"Suggested roadmap: {path}\n"
        f"Quiz bank: {quiz}\n"
    )
    return {"reply": safe_llm_invoke(prompt)}

def chitchat(state: Dict[str, Any]):
    msg = state.get("message", "")
    return {"reply": safe_llm_invoke(f"Answer briefly and helpfully: {msg}")}

def tts_node(state: Dict[str, Any]):
    text = state.get("reply", "")
    if not text:
        return {}
    return {"audio_b64": synthesize_audio(text)}

# ---- Build the graph ----
def build_graph():
    g = StateGraph(dict)
    g.add_node("router", router)
    g.add_node("career", career_agent)
    g.add_node("learning", learning_agent)
    g.add_node("chat", chitchat)
    g.add_node("tts", tts_node)

    g.set_entry_point("router")

    def route(state):
        intent = state.get("intent")
        if intent == "career":
            return "career"
        if intent == "learning":
            return "learning"
        return "chat"

    g.add_conditional_edges("router", route)
    g.add_edge("career", "tts")
    g.add_edge("learning", "tts")
    g.add_edge("chat", "tts")
    g.add_edge("tts", END)

    memory = MemorySaver()
    return g.compile(checkpointer=memory)

app_graph = build_graph()
