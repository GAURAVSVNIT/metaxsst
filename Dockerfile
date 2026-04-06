FROM python:3.11-slim

LABEL org.opencontainers.image.title="Government Fraud Detection — OpenEnv"
LABEL org.opencontainers.image.description="AI agent training environment for government fraud detection"
LABEL org.opencontainers.image.version="1.0.0"
LABEL space_sdk="docker"
LABEL tags="openenv"

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY models.py .
COPY environment.py .
COPY app.py .
COPY inference.py .
COPY openenv.yaml .
COPY data/ ./data/
COPY tasks/ ./tasks/

# Create __init__ files
RUN touch data/__init__.py tasks/__init__.py

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["python", "app.py"]
