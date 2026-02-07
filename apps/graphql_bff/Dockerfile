FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/graphql_bff/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common dependencies
COPY common/ ./common/

# Copy the service code
COPY apps/graphql_bff/ ./apps/graphql_bff/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8400

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8400/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "apps.graphql_bff.main:app", "--host", "0.0.0.0", "--port", "8400"]
