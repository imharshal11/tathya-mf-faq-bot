FROM python:3.11-slim

# Create non-root user with UID 1000 (Hugging Face default)
RUN useradd -m -u 1000 -s /bin/bash user

WORKDIR /home/user/app
ENV HOME=/home/user
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Pre-download ONNX embedding model during build
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()" 2>/dev/null || true

# Ensure user owns the app directory (so data/chroma can be written)
RUN chown -R user:user /home/user/app

USER user

EXPOSE 7860

CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-7860}"]