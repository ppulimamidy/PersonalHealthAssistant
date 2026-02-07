FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (copy entire apps and common directories)
COPY apps/ ./apps/
COPY common/ ./common/

# Create necessary directories
RUN mkdir -p logs uploads outputs models cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8007/ready || exit 1

# Run the application
CMD ["uvicorn", "apps.nutrition.main:app", "--host", "0.0.0.0", "--port", "8007"] 