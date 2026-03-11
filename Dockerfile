# ── Base: Python 3.10 slim + Node.js 18 + nginx + supervisord ────────────────
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl gnupg nginx supervisor && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python deps ───────────────────────────────────────────────────────────────
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# ── Node deps ─────────────────────────────────────────────────────────────────
COPY backend/package*.json /app/backend/
RUN cd /app/backend && npm install --omit=dev

# ── Source files ──────────────────────────────────────────────────────────────
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# ── Configs ───────────────────────────────────────────────────────────────────
COPY nginx.conf      /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/zoikon.conf

WORKDIR /app

# Cloud Run listens on 8080
EXPOSE 8080

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/zoikon.conf"]