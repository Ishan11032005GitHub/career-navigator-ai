# ---------- Base Image ----------
FROM ubuntu:22.04

# ---------- Prevent tzdata prompt (non-interactive setup) ----------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# ---------- System Setup ----------
RUN apt-get update && apt-get install -y \
    curl git python3 python3-pip texlive-latex-base texlive-latex-recommended \
    texlive-fonts-recommended texlive-latex-extra build-essential wget \
    poppler-utils libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ---------- Working Directory ----------
WORKDIR /app
COPY . .

# ---------- Install Python Dependencies ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Pre-pull model (adjust model name) ----------
# Avoid failing the build if model pull fails (e.g., network timeout)
RUN ollama pull gemma3:4b || true

# ---------- Expose Ports ----------
EXPOSE 8000
EXPOSE 11434

# ---------- Environment ----------
ENV OLLAMA_HOST=0.0.0.0:11434
ENV PYTHONUNBUFFERED=1

# ---------- Run Ollama + FastAPI ----------
CMD bash -c "ollama serve & sleep 8 && ollama pull gemma3:4b && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

