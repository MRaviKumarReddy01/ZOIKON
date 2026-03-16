# ── Zoiko Mobile Chatbot — Fixed Dockerfile ──────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

# ── Install dependencies ──────────────────────────────────────────────────────
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy backend source ───────────────────────────────────────────────────────
COPY backend/ backend/
RUN touch backend/__init__.py

# ── Copy frontend (CRITICAL: must be at /app/frontend) ───────────────────────
COPY frontend/ frontend/

# ── Verify frontend exists in container ───────────────────────────────────────
RUN if [ ! -f frontend/index.html ]; then \
      echo "ERROR: frontend/index.html not found!" && \
      ls -la frontend/ || echo "Frontend folder missing!"; \
    else \
      echo "✅ Frontend found: $(wc -c < frontend/index.html) bytes"; \
    fi

# ── Copy data folder ──────────────────────────────────────────────────────────
COPY data/ data/ 2>/dev/null || true

# ── Cloud Run configuration ───────────────────────────────────────────────────
ENV PORT=8080
EXPOSE 8080

# ── Start FastAPI server ──────────────────────────────────────────────────────
# Using JSON format to avoid shell issues
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
