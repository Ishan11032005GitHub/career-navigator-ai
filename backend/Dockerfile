FROM python:3.12-slim

WORKDIR /app
COPY . .

# Install LaTeX + build deps
RUN apt-get update && apt-get install -y \
    texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra \
    build-essential python3-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
