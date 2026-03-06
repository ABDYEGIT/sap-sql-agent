# ══════════════════════════════════════════════════════════════════
# Yorglass IK Chatbot API - Docker Image
# ══════════════════════════════════════════════════════════════════
# Build:  docker build -t yorglass-chatbot .
# Run:    docker run -d -p 8000:8000 --env-file .env --name ik-chatbot yorglass-chatbot
# Logs:   docker logs ik-chatbot
# Stop:   docker stop ik-chatbot
# ══════════════════════════════════════════════════════════════════

FROM python:3.12-slim

# Calisma dizini
WORKDIR /app

# Sistem bagimliliklar (chromadb icin build-essential gerekli)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Once requirements.txt kopyala (Docker cache icin)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarini kopyala
COPY api_server.py .
COPY config.py .
COPY rag_engine.py .
COPY token_tracker.py .
COPY ik_agent/ ./ik_agent/

# Port
EXPOSE 8000

# Sunucuyu baslat
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
