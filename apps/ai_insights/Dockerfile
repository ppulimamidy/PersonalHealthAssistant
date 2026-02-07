FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/ai_insights/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/ai_insights/ ./apps/ai_insights/
COPY common/ ./common/
COPY apps/__init__.py ./apps/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8200/health || exit 1

# Run the application
CMD ["uvicorn", "apps.ai_insights.main:app", "--host", "0.0.0.0", "--port", "8200"] 