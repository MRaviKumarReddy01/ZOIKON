# ── Zoiko Mobile Chatbot — Dockerfile ─────────────────────────────────────────
# Repo structure:
#   backend/app.py          ← FastAPI app
#   backend/__init__.py     ← makes it a Python package (create if missing)
#   knowledge.json          ← chatbot knowledge (at repo root)
#   index.html              ← frontend  (at repo root)
#   requirements.txt        ← at repo root
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.10-slim

WORKDIR /app

# ── Install dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Copy backend source ────────────────────────────────────────────────────────
COPY backend/ backend/

# ── Ensure backend is a Python package ────────────────────────────────────────
RUN touch backend/__init__.py

# ── Copy frontend HTML (FastAPI mounts /frontend as static) ───────────────────
RUN mkdir -p frontend
COPY index.html frontend/index.html

# ── Copy knowledge base into data/ (where app.py reads it) ────────────────────
RUN mkdir -p data
COPY knowledge.json data/knowledge.json

# ── Run retrain.py on each build so knowledge is baked in ─────────────────────
COPY retrain.py .
RUN python retrain.py

# ── Cloud Run listens on $PORT (default 8080) ─────────────────────────────────
ENV PORT=8080
EXPOSE 8080

# ── Launch FastAPI via uvicorn ─────────────────────────────────────────────────
CMD exec uvicorn backend.app:app \
      --host 0.0.0.0 \
      --port ${PORT} \
      --workers 1 \
      --log-level info
