FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
COPY apps/mvp_api/requirements.txt ./mvp_api_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r mvp_api_requirements.txt

# Copy common directory
COPY common/ ./common/

# Copy device_data for Oura client
COPY apps/device_data/ ./apps/device_data/

# Copy MVP API application
COPY apps/mvp_api/ ./apps/mvp_api/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "apps.mvp_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
