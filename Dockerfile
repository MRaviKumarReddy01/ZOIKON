# ── Zoiko Mobile Chatbot — Production Dockerfile ──────────────────────────────
# Multi-stage build for a lean final image

# ── Stage 1: dependency builder ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="support@zoikomobile.com"
LABEL app="zoikon-chatbot"

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# ── Copy application source ────────────────────────────────────────────────────
COPY app.py .
COPY retrain.py .

# ── Create data directory and seed knowledge base ─────────────────────────────
RUN mkdir -p data
COPY knowledge.json data/knowledge.json

# ── Create frontend directory and copy HTML ────────────────────────────────────
RUN mkdir -p frontend
COPY index.html frontend/index.html

# ── Run knowledge retraining on each build ────────────────────────────────────
RUN python retrain.py

# ── Cloud Run listens on PORT env var (default 8080) ──────────────────────────
ENV PORT=8080
EXPOSE 8080

# ── Non-root user for security ────────────────────────────────────────────────
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# ── SMTP credentials injected at runtime via Cloud Run env vars ───────────────
# (do NOT bake secrets into the image)
# ENV SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SUPPORT_EMAIL
# are set in Cloud Run service configuration / GitHub Actions secrets

# ── Start server ──────────────────────────────────────────────────────────────
CMD exec uvicorn app:app \
      --host 0.0.0.0 \
      --port ${PORT} \
      --workers 2 \
      --log-level info