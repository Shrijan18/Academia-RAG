FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio & document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight CPU-only PyTorch first (saves 2.5 GB of CUDA libs and ~350 MB RAM)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Pre-download SentenceTransformer all-MiniLM-L6-v2 during Docker build phase
# This prevents downloading model weights at runtime and eliminates boot timeouts
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend and data folders
COPY backend /app/backend
COPY Data /app/Data

WORKDIR /app/backend

# Optimize environment for low-memory container
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

EXPOSE 10000

# Launch Gunicorn with single worker for low-memory footprint
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 300 api:app"]
