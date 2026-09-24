FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (fast download from official CPU wheel, ~150MB instead of 2GB CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining AI dependencies
COPY requirements-llm.txt .
RUN pip install --no-cache-dir -r requirements-llm.txt flask-cors

# Copy training files containing the model adapter and inference code
COPY training/ training/

# Hugging Face Spaces environment setup
ENV HOST=0.0.0.0
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# Start Financial Advisor AI server
CMD ["python", "training/serve_llm.py"]
