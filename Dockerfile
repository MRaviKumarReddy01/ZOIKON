# ── Base: Python 3.10 slim ────────────────────────────────────────────────────
FROM python:3.10-slim

# ── Install dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Set working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Copy requirements and install Python deps ─────────────────────────────────
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application files ────────────────────────────────────────────────────
COPY backend/app.py .
COPY frontend/ ./frontend/
COPY data/ ./data/ 2>/dev/null || true

# ── Cloud Run expects port 8080 ───────────────────────────────────────────────
EXPOSE 8080

# ── Run FastAPI application ───────────────────────────────────────────────────
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
