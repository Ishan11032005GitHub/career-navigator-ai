# ---------- Base Image ----------
FROM ubuntu:22.04

# ---------- System Setup ----------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl git python3 python3-pip build-essential wget \
    texlive-latex-base texlive-latex-recommended \
    texlive-fonts-recommended texlive-latex-extra tzdata && \
    rm -rf /var/lib/apt/lists/*

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ---------- Working Directory ----------
WORKDIR /app/backend
COPY . .

# ---------- Install Python Dependencies ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Expose Ports ----------
EXPOSE 8000
EXPOSE 11434

# ---------- Start Ollama + FastAPI ----------
CMD bash -c "\
ollama serve & \
sleep 8 && \
ollama pull gemma3:4b || true && \
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} \
"
