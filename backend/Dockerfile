# ---------- Base Image ----------
FROM ubuntu:22.04

# ---------- Prevent tzdata prompts ----------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# ---------- System Setup ----------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl git python3 python3-pip texlive-latex-base texlive-latex-recommended \
    texlive-fonts-recommended texlive-latex-extra build-essential wget tzdata \
    && rm -rf /var/lib/apt/lists/*

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ---------- Working Directory ----------
WORKDIR /app
COPY . .

# ---------- Install Python Dependencies ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Pre-pull the model ----------
# This ensures gemma3:4b exists before the container starts
RUN ollama serve & \
    sleep 15 && \
    ollama pull gemma3:4b || true

# ---------- Expose Ports ----------
EXPOSE 8000
EXPOSE 11434

# ---------- Start Ollama + FastAPI ----------
# Run Ollama in background, then FastAPI
CMD bash -c "\
ollama serve & \
sleep 5 && \
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} \
"
