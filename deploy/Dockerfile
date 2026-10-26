# Backend image. Build from the repository root:
#   docker build -f deploy/Dockerfile -t ait-backend .
# NOTE: written without a local Docker install; test before production use.
FROM python:3.12-slim

# OpenCV runtime libraries.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    UPLOAD_FOLDER=/data/uploads

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt "psycopg[binary]"

COPY ai ai
COPY backend backend
RUN python ai/scripts/download_pose_model.py \
    && useradd --create-home --uid 10001 ait \
    && mkdir -p /data/uploads \
    && chown -R ait /data

USER ait
WORKDIR /app/backend
EXPOSE 8000

# Behind the reverse proxy: trust its X-Forwarded-* headers so rate limits
# see the real client IP.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
