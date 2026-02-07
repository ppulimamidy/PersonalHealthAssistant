# Knowledge Graph Service Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY apps/knowledge_graph/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY common/ ./common/

# Copy knowledge graph service
COPY apps/knowledge_graph/ ./apps/knowledge_graph/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Run the application
CMD ["uvicorn", "apps.knowledge_graph.main:app", "--host", "0.0.0.0", "--port", "8010"] 