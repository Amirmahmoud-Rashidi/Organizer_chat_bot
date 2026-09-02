# =============================================================================
# Organizer Chat Bot — Dockerfile
# Slim Python 3.11 image, no system dependencies required (telethon is pure
# Python; python-telegram-bot uses asyncio; google-genai and openai are pure
# Python too).
# =============================================================================
FROM python:3.11-slim

# Avoid interactive prompts during apt operations.
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first (better Docker layer caching).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source.
COPY src ./src
COPY pyproject.toml ./

# Drop privileges for safety.
RUN useradd --create-home --shell /bin/bash botuser \
 && chown -R botuser:botuser /app
USER botuser

# Persistent volume for Telethon session files (.session) and any logs.
# docker-compose.yml mounts this.
VOLUME ["/app/data"]

WORKDIR /app
EXPOSE 0

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "-m", "src.main"]