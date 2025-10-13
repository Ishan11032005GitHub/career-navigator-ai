import os, shutil
from fastapi import (
    FastAPI, HTTPException, Depends, Form,
    UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from graph import career_agent, learning_agent
from auth import (
    create_token, verify_token,
    hash_password, verify_password,
    create_reset_token, verify_reset_token
)
from database import get_db

# ==========================================================
# ---------------------- INIT APP --------------------------
# ==========================================================
load_dotenv()
app = FastAPI(title="Career Navigator AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

print("✅ Using LLM:", os.getenv("OLLAMA_MODEL", "llama3"))

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ==========================================================
# ---------------------- AUTH ROUTES ------------------------
# ==========================================================
@app.post("/api/signup")
def signup(user: dict):
    email, username, password = user.get("email"), user.get("username"), user.get("password")
    if not all([email, username, password]):
        raise HTTPException(status_code=400, detail="Missing fields")

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, username, password) VALUES (?,?,?)",
                    (email, username, hash_password(password)))
        conn.commit()
        return {"msg": "Signup successful"}
    except Exception:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    finally:
        conn.close()


@app.post("/api/login")
def login(user: dict):
    email, password = user.get("email"), user.get("password")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    row = cur.fetchone(); conn.close()
    if not row or not verify_password(password, row["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(row["username"])
    return {"token": token, "username": row["username"]}


@app.post("/api/forgot")
def forgot(user: dict):
    email = user.get("email")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Email not found")
    token = create_reset_token(email)
    return {"reset_token": token, "msg": "Use this token to reset password"}


@app.post("/api/reset")
def reset(data: dict):
    token, new_pass = data.get("token"), data.get("new_password")
    email = verify_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET password=? WHERE email=?", (hash_password(new_pass), email))
    conn.commit(); conn.close()
    return {"msg": "Password updated successfully"}


# ==========================================================
# ------------------ EXISTING AI ROUTES --------------------
# ==========================================================
@app.post("/api/career", response_model=ChatResponse)
def career(req: ChatRequest, user=Depends(verify_token)):
    """
    Handles career guidance requests.
    Supports resume text or uploaded resume file path.
    """
    data = req.dict()
    result = career_agent(data)
    return ChatResponse(reply=result.get("reply", ""))


@app.post("/api/learning", response_model=ChatResponse)
def learning(req: ChatRequest, user=Depends(verify_token)):
    result = learning_agent(req.dict(), thread_id=req.thread_id)
    return ChatResponse(reply=result.get("reply", ""))


# ==========================================================
# ---------------------- JOB ROUTES ------------------------
# ==========================================================
@app.post("/api/jobs/add")
def add_job(job: dict, user=Depends(verify_token)):
    title = job.get("title")
    company = job.get("company")
    location = job.get("location", "")
    description = job.get("description", "")
    link = job.get("link", "")

    if not title or not company:
        raise HTTPException(status_code=400, detail="Title and company are required")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (title, company, location, description, link)
        VALUES (?, ?, ?, ?, ?)
    """, (title, company, location, description, link))
    conn.commit()
    conn.close()

    return {"msg": "Job added successfully"}


@app.get("/api/jobs")
def get_jobs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY posted_at DESC")
    jobs = cur.fetchall()
    conn.close()
    return {"jobs": [dict(row) for row in jobs]}


@app.post("/api/jobs/save")
def save_job(data: dict, user=Depends(verify_token)):
    username = user
    job_id = data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="Missing job_id")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_row["id"]

    try:
        cur.execute("INSERT INTO saved_jobs (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
        conn.commit()
        msg = "Job saved successfully"
    except:
        msg = "Job already saved"
    finally:
        conn.close()

    return {"msg": msg}


@app.get("/api/jobs/saved")
def get_saved_jobs(user=Depends(verify_token)):
    username = user
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_row["id"]

    cur.execute("""
        SELECT jobs.* FROM jobs
        JOIN saved_jobs ON jobs.id = saved_jobs.job_id
        WHERE saved_jobs.user_id=?
        ORDER BY saved_jobs.saved_at DESC
    """, (user_id,))
    saved = cur.fetchall()
    conn.close()
    return {"saved_jobs": [dict(row) for row in saved]}


@app.post("/api/jobs/apply")
async def apply_to_job(
    job_id: int = Form(...),
    resume: UploadFile = File(...),
    user=Depends(verify_token)
):
    username = user
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes allowed")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_row["id"]

    filename = f"{username}_{job_id}_{resume.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    cur.execute("""
        INSERT INTO applications (user_id, job_id, resume_path)
        VALUES (?, ?, ?)
    """, (user_id, job_id, f"/uploads/{filename}"))
    conn.commit()
    conn.close()

    return {"msg": "Application submitted successfully!", "resume": f"/uploads/{filename}"}


@app.get("/api/jobs/applications")
def get_applications(user=Depends(verify_token)):
    username = user
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user_row["id"]

    cur.execute("""
        SELECT jobs.title, jobs.company, jobs.location,
               applications.resume_path, applications.applied_at
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        WHERE applications.user_id=?
        ORDER BY applications.applied_at DESC
    """, (user_id,))
    apps = cur.fetchall()
    conn.close()
    return {"applications": [dict(row) for row in apps]}


# ==========================================================
# ------------------- RESUME UPLOAD ------------------------
# ==========================================================
@app.post("/api/resume/upload")
async def upload_resume(resume: UploadFile = File(...), user=Depends(verify_token)):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    filename = f"{user}_resume_{resume.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    return {"msg": "Resume uploaded successfully!", "path": f"/uploads/{filename}"}


# ==========================================================
# ---------------------- ROOT ------------------------------
# ==========================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "Career Navigator AI Backend Active"}
