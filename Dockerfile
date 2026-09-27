FROM python:3.11-slim

# Create non-root user with UID 1000 (Hugging Face default)
RUN useradd -m -u 1000 -s /bin/bash user

WORKDIR /home/user/app
ENV HOME=/home/user
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Small-server settings to reduce memory
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false
ENV ANONYMIZED_TELEMETRY=False

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Ensure user owns the app directory and cache directory (so data/chroma and .cache can be written)
RUN chown -R user:user /home/user

USER user

# Pre-download ONNX embedding model during build (runs as user, saves to /home/user/.cache/chroma)
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()" 2>/dev/null || true

# Build the index at build time (runs as user)
RUN python -m src.ingest

EXPOSE 7860

# Single worker, no reload for low memory
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]