# ---------- Base Image ----------
FROM python:3.11-slim

# ---------- System Setup ----------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install only what’s necessary
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl git texlive-xetex texlive-fonts-recommended && \
    rm -rf /var/lib/apt/lists/*

# ---------- Install Ollama ----------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ---------- Working Directory ----------
WORKDIR /app

# Copy backend code and requirements
COPY backend/ ./backend/

# ---------- Install Python Dependencies ----------
RUN pip install --no-cache-dir -r backend/requirements.txt

# ---------- Expose Ports ----------
EXPOSE 8000
EXPOSE 11434

# ---------- Start Ollama + FastAPI ----------
CMD bash -c "\
ollama serve & \
sleep 10 && \
ollama pull gemma3:4b || true && \
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
