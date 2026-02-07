FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/ ./apps/
COPY common/ ./common/

# Create necessary directories
RUN mkdir -p logs uploads outputs models cache

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "apps.health_analysis.main:app", "--host", "0.0.0.0", "--port", "8008"] 