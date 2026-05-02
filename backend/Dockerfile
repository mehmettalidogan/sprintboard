# ════════════════════════════════════════════════════════════════════════════
# SprintBoard AI — Multi-stage Dockerfile
#
# Stage 1 (builder): Install all Python dependencies into an isolated venv.
# Stage 2 (runtime): Copy only the venv and application code into a slim
#                    final image, keeping the attack surface minimal.
#
# Build:
#   docker build -t sprintboard-api:latest .
#
# Run (standalone, without Compose):
#   docker run --env-file .env -p 8000:8000 sprintboard-api:latest
# ════════════════════════════════════════════════════════════════════════════

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Prevent .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install OS-level build dependencies (needed by asyncpg, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first — leverages Docker layer cache
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Runtime OS dependencies only (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN addgroup --system sprintboard && adduser --system --ingroup sprintboard sprintboard

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY ./app ./app

# Copy Alembic migration files
COPY alembic.ini .
COPY ./alembic ./alembic

# Copy and prepare entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure the non-root user owns the working directory
RUN chown -R sprintboard:sprintboard /app /entrypoint.sh

USER sprintboard

# Expose API port
EXPOSE 8000

# Health check (Docker Engine will mark the container unhealthy if this fails)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Entrypoint: alembic upgrade head → uvicorn
ENTRYPOINT ["/entrypoint.sh"]
