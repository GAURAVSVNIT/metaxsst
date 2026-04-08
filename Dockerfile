FROM python:3.11-slim

LABEL org.opencontainers.image.title="Government Fraud Detection — OpenEnv"
LABEL org.opencontainers.image.description="AI agent training environment for government fraud detection"
LABEL org.opencontainers.image.version="1.0.0"
LABEL space_sdk="docker"
LABEL tags="openenv"

USER root
# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv globally
RUN pip install --no-cache-dir uv

# Install Python dependencies using uv as root
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Now create and switch to the non-root user required by HF
RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy application code from backend directory (and inference from root)
COPY --chown=user backend/models.py .
COPY --chown=user backend/environment.py .
COPY --chown=user backend/app.py .
COPY --chown=user inference.py .
COPY --chown=user backend/openenv.yaml .
COPY --chown=user backend/data/ ./data/
COPY --chown=user backend/tasks/ ./tasks/

# Create __init__ files
RUN touch data/__init__.py tasks/__init__.py

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
