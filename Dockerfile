FROM python:3.13-slim

# ============================================================
# ENVIRONMENT
# ============================================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ============================================================
# WORKING DIRECTORY
# ============================================================

WORKDIR /app

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================
# APPLICATION
# ============================================================

COPY . .

# ============================================================
# NON-ROOT USER
# ============================================================

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app

USER appuser

# ============================================================
# API PORT
# ============================================================

EXPOSE 8000

# ============================================================
# CONTAINER HEALTH CHECK
# ============================================================

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# ============================================================
# START API
# ============================================================

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]