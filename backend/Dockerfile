# ---------- Base Image ----------
FROM ubuntu:22.04

# ---------- System Setup ----------
RUN apt-get update && apt-get install -y \
    curl git python3 python3-pip texlive-latex-base texlive-latex-recommended \
    texlive-fonts-recommended texlive-latex-extra build-essential wget \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ---------- Working Directory ----------
WORKDIR /app
COPY . .

# ---------- Install Python Dependencies ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Pre-pull model (adjust model name) ----------
RUN ollama pull gemma3:4b || true

# ---------- Expose Port ----------
EXPOSE 8000
EXPOSE 11434

# ---------- Run Ollama + FastAPI ----------
CMD bash -c "ollama serve & sleep 5 && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
