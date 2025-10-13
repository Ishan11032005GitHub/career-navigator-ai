import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

# Create applications table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    job_id INTEGER,
    resume_path TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
""")

conn.commit()
conn.close()
print("✅ 'applications' table created successfully!")