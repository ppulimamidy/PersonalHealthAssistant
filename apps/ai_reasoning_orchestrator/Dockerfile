FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/ai_reasoning_orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common dependencies
COPY common/ ./common/

# Copy the service code
COPY apps/ai_reasoning_orchestrator/ ./apps/ai_reasoning_orchestrator/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8300/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "apps.ai_reasoning_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8300"]
