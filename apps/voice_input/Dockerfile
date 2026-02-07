# Voice Input Service Dockerfile - Minimal Version

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and vision analysis
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    portaudio19-dev \
    python3-dev \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libx264-dev \
    libx265-dev \
    libvpx-dev \
    libwebp-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints, then install packages
# Explicitly exclude main requirements.txt by copying only voice input requirements
COPY apps/voice_input/voice_input.requirements.txt ./voice_input.requirements.txt
# COPY constraints.txt ./constraints.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r voice_input.requirements.txt

# After pip install requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy only the voice input service and common files
COPY apps/voice_input/ ./apps/voice_input/
COPY common/ ./common/
# COPY apps/__init__.py ./apps/

# Create necessary directories
RUN mkdir -p /app/uploads/audio /app/uploads/images /app/temp /app/outputs/vision_analysis

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (will be overridden by environment variable)
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["uvicorn", "apps.voice_input.main:app", "--host", "0.0.0.0", "--port", "8003"] 