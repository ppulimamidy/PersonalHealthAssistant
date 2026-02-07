FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY apps/medical_analysis/ ./apps/medical_analysis/
COPY common/ ./common/
COPY apps/__init__.py ./apps/

# Create necessary directories
RUN mkdir -p logs uploads outputs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8006/ready || exit 1

# Run the application
CMD ["uvicorn", "apps.medical_analysis.main:app", "--host", "0.0.0.0", "--port", "8006"] 