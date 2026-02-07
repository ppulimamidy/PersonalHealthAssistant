# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV AUTH_SERVICE_URL="http://personalhealthassistant-auth-service:8000"
ENV USER_PROFILE_SERVICE_URL="http://personalhealthassistant-user-profile-service:8001"
ENV HEALTH_TRACKING_SERVICE_URL="http://personalhealthassistant-health-tracking-service:8002"
ENV DEVICE_DATA_SERVICE_URL="http://personalhealthassistant-device-data-service:8004"
ENV KAFKA_BOOTSTRAP_SERVERS="personalhealthassistant-kafka-1:9092"
ENV REDIS_URL="redis://redis:6379/0"
ENV DATABASE_URL="postgresql://postgres:your-super-secret-and-long-postgres-password@postgres-health-assistant:5432/health_assistant"
ENV EPIC_FHIR_CLIENT_ID="${EPIC_FHIR_CLIENT_ID:-}"
ENV EPIC_FHIR_CLIENT_SECRET="***REMOVED***"
ENV EPIC_FHIR_ENVIRONMENT="sandbox"
ENV EPIC_FHIR_REDIRECT_URI="http://localhost:5173/epic-fhir-callback.html"

# Install system dependencies including Tesseract OCR and basic DICOM libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    libdcmtk-dev \
    libgdcm-dev \
    libopencv-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY apps/medical_records/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/medical_records/ ./apps/medical_records/
COPY common/ ./common/
COPY apps/__init__.py ./apps/

# Create uploads directories
RUN mkdir -p /app/uploads/medical_documents/temp \
    /app/uploads/medical_documents/processed \
    /app/uploads/medical_documents/archived \
    /app/uploads/medical_images/dicom \
    /app/uploads/medical_images/converted \
    /app/uploads/medical_images/thumbnails \
    /app/uploads/medical_images/temp

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Run the application from the medical_records directory
WORKDIR /app/apps/medical_records
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
