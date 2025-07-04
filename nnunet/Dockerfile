# Use official PyTorch CUDA 11.8 base image with Python 3.10
FROM pytorch/pytorch:2.5.1-cuda11.8-cudnn9-runtime

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install basic system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone and install nnUNet
RUN git clone https://github.com/MIC-DKFZ/nnUNet.git /opt/nnUNet
WORKDIR /opt/nnUNet
RUN pip install --upgrade pip && pip install -e .

# Install FastAPI and dependencies
RUN pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    google-cloud-storage==2.14.0 

# VAR ENV NOT USE JUST FOR INIT
ENV nnUNet_raw="None" 
ENV nnUNet_preprocessed="None"
ENV nnUNet_results="None"

# Create app directory
WORKDIR /app

# Copy application code
COPY app.py /app/app.py

# Create necessary directories and copy model data
RUN mkdir -p /app/dataset
COPY nnUNet_trained_models /app/dataset/nnUNet_trained_models

# Expose port (Vertex AI uses 8080 by default)
EXPOSE 8080

# Health check (Vertex AI utilise le port 8080)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]