FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio & document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend and data folders
COPY backend /app/backend
COPY Data /app/Data

# Set working directory to backend
WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Launch Gunicorn server
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 180 api:app
