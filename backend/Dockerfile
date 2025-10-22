# ---------- Base Image ----------
FROM python:3.11-slim

# ---------- Set Working Directory ----------
WORKDIR /app
COPY . .

# ---------- Install System Dependencies ----------
# texlive packages → required for LaTeX PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra \
    build-essential python3-dev git wget curl \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# ---------- Expose Port ----------
EXPOSE 8000

# ---------- Run the App ----------
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
