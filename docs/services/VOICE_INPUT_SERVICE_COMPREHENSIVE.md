# Voice Input Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)

## Overview

The Voice Input Service provides advanced speech-to-text capabilities, natural language processing, and voice command interpretation for the Personal Health Assistant platform. It enables users to interact with the platform using voice commands, making it more accessible and user-friendly.

### Key Responsibilities
- Speech-to-text conversion
- Natural language processing and understanding
- Voice command interpretation
- Audio file processing and analysis
- Multi-language support
- Real-time voice streaming
- Voice biometrics and speaker identification

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │  Voice Input    │
│                 │    │   (Traefik)     │    │   Service       │
│ - Mobile App    │───▶│                 │───▶│                 │
│ - Web App       │    │ - Rate Limiting │    │ - Speech-to-    │
│ - IoT Devices   │    │ - SSL/TLS       │    │   Text          │
│ - Smart Speakers│    │                 │    │ - NLP           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Audio Files   │
                                              │ - Transcriptions│
                                              │ - Voice Models  │
                                              │ - User Profiles │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   File Storage  │
                                              │                 │
                                              │ - Audio Files   │
                                              │ - Processed     │
                                              │   Audio         │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Speech Recognition**: Whisper, Google Speech-to-Text
- **NLP**: spaCy, NLTK, Transformers
- **Audio Processing**: librosa, pydub
- **Storage**: PostgreSQL + File system
- **Real-time**: WebSocket support for streaming

## Features

### 1. Speech-to-Text Conversion
- **Real-time Transcription**: Live audio streaming and transcription
- **Batch Processing**: Process pre-recorded audio files
- **Multi-language Support**: Support for 50+ languages
- **Accent Recognition**: Handle various accents and dialects
- **Noise Reduction**: Advanced noise filtering and audio enhancement
- **Speaker Diarization**: Identify different speakers in audio

### 2. Natural Language Processing
- **Intent Recognition**: Understand user intentions from voice input
- **Entity Extraction**: Extract relevant information (dates, numbers, names)
- **Sentiment Analysis**: Analyze emotional tone and sentiment
- **Context Understanding**: Maintain conversation context
- **Command Parsing**: Parse voice commands for system actions
- **Language Detection**: Automatic language detection

### 3. Voice Commands & Control
- **Health Commands**: Voice commands for health tracking
- **Navigation Commands**: Voice navigation through the app
- **Data Entry**: Voice-based data input for health metrics
- **Emergency Commands**: Voice-activated emergency features
- **Accessibility**: Voice commands for accessibility features
- **Custom Commands**: User-defined voice commands

### 4. Audio Processing
- **Audio Format Support**: MP3, WAV, FLAC, M4A, OGG
- **Audio Quality Enhancement**: Noise reduction, echo cancellation
- **Audio Segmentation**: Split long audio into manageable chunks
- **Audio Compression**: Optimize audio for processing
- **Audio Validation**: Validate audio quality and format

### 5. Voice Biometrics
- **Speaker Identification**: Identify users by voice
- **Voice Authentication**: Secure voice-based authentication
- **Voice Profile Management**: Store and manage voice profiles
- **Voice Cloning Detection**: Detect synthetic or cloned voices
- **Voice Health Monitoring**: Monitor voice health indicators

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **WebSockets**: Real-time communication
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database

### Speech Recognition
- **OpenAI Whisper**: Advanced speech recognition
- **Google Speech-to-Text**: Cloud-based speech recognition
- **Mozilla DeepSpeech**: Open-source speech recognition
- **Vosk**: Offline speech recognition

### Natural Language Processing
- **spaCy**: Industrial-strength NLP
- **NLTK**: Natural language toolkit
- **Transformers**: Hugging Face transformers
- **BERT/RoBERTa**: Pre-trained language models

### Audio Processing
- **librosa**: Audio and music analysis
- **pydub**: Audio manipulation
- **soundfile**: Audio file I/O
- **webrtcvad**: Voice activity detection

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **websockets**: WebSocket support
- **redis**: Caching and session management

## API Endpoints

### Speech-to-Text

#### POST /api/v1/speech/transcribe
Transcribe audio file to text.

**Request:**
```
Content-Type: multipart/form-data
audio_file: <file>
language: en
model: whisper-large
```

**Response:**
```json
{
  "transcription_id": "uuid",
  "text": "Hello, I need to log my blood pressure reading",
  "confidence": 0.95,
  "language": "en",
  "duration_seconds": 3.2,
  "words": [
    {
      "word": "Hello",
      "start_time": 0.0,
      "end_time": 0.5,
      "confidence": 0.98
    }
  ],
  "speakers": [
    {
      "speaker_id": 1,
      "segments": [
        {
          "start_time": 0.0,
          "end_time": 3.2,
          "text": "Hello, I need to log my blood pressure reading"
        }
      ]
    }
  ]
}
```

#### POST /api/v1/speech/transcribe-stream
Real-time streaming transcription.

**WebSocket Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8003/api/v1/speech/transcribe-stream');
ws.send(audioChunk); // Send audio data
```

#### GET /api/v1/speech/transcriptions
Get transcription history.

#### GET /api/v1/speech/transcriptions/{transcription_id}
Get specific transcription details.

### Natural Language Processing

#### POST /api/v1/nlp/analyze
Analyze text for intent and entities.

**Request Body:**
```json
{
  "text": "I need to log my blood pressure reading of 120 over 80",
  "context": "health_tracking"
}
```

**Response:**
```json
{
  "intent": "log_health_metric",
  "confidence": 0.92,
  "entities": [
    {
      "type": "health_metric",
      "value": "blood_pressure",
      "confidence": 0.95
    },
    {
      "type": "number",
      "value": "120",
      "role": "systolic",
      "confidence": 0.98
    },
    {
      "type": "number",
      "value": "80",
      "role": "diastolic",
      "confidence": 0.98
    }
  ],
  "sentiment": {
    "polarity": "neutral",
    "confidence": 0.85
  }
}
```

#### POST /api/v1/nlp/commands
Process voice commands.

**Request Body:**
```json
{
  "command": "log my weight as 70 kilograms",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "action": "log_weight",
  "parameters": {
    "weight": 70,
    "unit": "kg"
  },
  "confidence": 0.94,
  "response": "I've logged your weight as 70 kilograms"
}
```

### Voice Commands

#### GET /api/v1/commands
Get available voice commands.

#### POST /api/v1/commands
Create custom voice command.

**Request Body:**
```json
{
  "trigger_phrase": "check my heart rate",
  "action": "get_heart_rate",
  "description": "Get current heart rate reading"
}
```

#### PUT /api/v1/commands/{command_id}
Update voice command.

#### DELETE /api/v1/commands/{command_id}
Delete voice command.

### Voice Biometrics

#### POST /api/v1/voice/enroll
Enroll user voice for biometric identification.

**Request:**
```
Content-Type: multipart/form-data
audio_file: <file>
user_id: uuid
phrase: "My voice is my password"
```

#### POST /api/v1/voice/verify
Verify user identity using voice.

**Request:**
```
Content-Type: multipart/form-data
audio_file: <file>
user_id: uuid
```

**Response:**
```json
{
  "verified": true,
  "confidence": 0.87,
  "match_score": 0.92
}
```

#### GET /api/v1/voice/profile
Get user's voice profile.

#### DELETE /api/v1/voice/profile
Delete user's voice profile.

### Audio Processing

#### POST /api/v1/audio/enhance
Enhance audio quality.

**Request:**
```
Content-Type: multipart/form-data
audio_file: <file>
enhancement_type: noise_reduction
```

#### POST /api/v1/audio/segment
Segment audio into chunks.

#### POST /api/v1/audio/convert
Convert audio format.

### Real-time Communication

#### WebSocket /api/v1/stream/voice
Real-time voice streaming endpoint.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8003/api/v1/stream/voice');

ws.onopen = () => {
  console.log('Connected to voice stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.transcription);
};

// Send audio data
ws.send(audioChunk);
```

## Data Models

### Transcription Model
```python
class Transcription(Base):
    __tablename__ = "transcriptions"
    __table_args__ = {'schema': 'voice_input'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    audio_file_path = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    language = Column(String(10), nullable=False)
    model_used = Column(String(50), nullable=False)
    
    duration_seconds = Column(Float)
    word_count = Column(Integer)
    
    # Detailed transcription data
    words = Column(JSON)  # Word-level timestamps and confidence
    speakers = Column(JSON)  # Speaker diarization data
    
    # Metadata
    file_size_bytes = Column(BigInteger)
    audio_format = Column(String(20))
    sample_rate = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
```

### Voice Command Model
```python
class VoiceCommand(Base):
    __tablename__ = "voice_commands"
    __table_args__ = {'schema': 'voice_input'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    trigger_phrase = Column(String(200), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Command parameters
    parameters = Column(JSON, default=dict)
    response_template = Column(Text)
    
    is_active = Column(Boolean, default=True)
    is_system_command = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Voice Profile Model
```python
class VoiceProfile(Base):
    __tablename__ = "voice_profiles"
    __table_args__ = {'schema': 'voice_input'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Voice characteristics
    voice_embedding = Column(JSON)  # Voice feature vector
    voice_characteristics = Column(JSON)  # Pitch, tone, etc.
    
    # Enrollment data
    enrollment_audio_path = Column(String(500))
    enrollment_phrase = Column(String(200))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    
    # Verification settings
    verification_threshold = Column(Float, default=0.8)
    max_verification_attempts = Column(Integer, default=3)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### NLP Analysis Model
```python
class NLPAnalysis(Base):
    __tablename__ = "nlp_analyses"
    __table_args__ = {'schema': 'voice_input'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcription_id = Column(UUID(as_uuid=True), ForeignKey("voice_input.transcriptions.id"))
    
    intent = Column(String(100))
    intent_confidence = Column(Float)
    
    entities = Column(JSON)  # Extracted entities
    sentiment = Column(JSON)  # Sentiment analysis results
    
    context = Column(String(100))
    language = Column(String(10))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=voice-input-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# File Storage Configuration
UPLOAD_DIR=/app/uploads/audio
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_AUDIO_FORMATS=["mp3", "wav", "flac", "m4a", "ogg"]

# Speech Recognition Configuration
WHISPER_MODEL=whisper-large
GOOGLE_SPEECH_CREDENTIALS_PATH=/path/to/credentials.json
DEEP_SPEECH_MODEL_PATH=/path/to/model.pbmm

# NLP Configuration
SPACY_MODEL=en_core_web_lg
NLTK_DATA_PATH=/app/nltk_data
TRANSFORMERS_CACHE_DIR=/app/transformers_cache

# Voice Biometrics Configuration
VOICE_VERIFICATION_THRESHOLD=0.8
VOICE_ENROLLMENT_SAMPLES=3
VOICE_EMBEDDING_DIMENSION=512

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002

# WebSocket Configuration
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_HEARTBEAT_INTERVAL=30

# Processing Configuration
AUDIO_CHUNK_SIZE=1024
MAX_AUDIO_DURATION=300  # 5 minutes
BATCH_SIZE=10
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP models
RUN python -m spacy download en_core_web_lg
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads/audio

EXPOSE 8003

CMD ["uvicorn", "apps.voice_input.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Docker Compose
```yaml
voice-input-service:
  build:
    context: .
    dockerfile: apps/voice_input/Dockerfile
  ports:
    - "8003:8003"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
  volumes:
    - ./uploads:/app/uploads
    - ./models:/app/models
  depends_on:
    - postgres
    - redis
    - auth-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_speech.py
import pytest
from fastapi.testclient import TestClient
from apps.voice_input.main import app

client = TestClient(app)

def test_transcribe_audio():
    headers = {"Authorization": "Bearer test-token"}
    with open("test_audio.wav", "rb") as f:
        files = {"audio_file": f}
        response = client.post("/api/v1/speech/transcribe", files=files, headers=headers)
    assert response.status_code == 201
    assert "text" in response.json()

def test_nlp_analysis():
    headers = {"Authorization": "Bearer test-token"}
    data = {"text": "I need to log my blood pressure", "context": "health_tracking"}
    response = client.post("/api/v1/nlp/analyze", json=data, headers=headers)
    assert response.status_code == 200
    assert "intent" in response.json()
```

### Integration Tests
```python
# tests/integration/test_voice_commands.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_voice_command_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create voice command
        command_data = {
            "trigger_phrase": "log my weight",
            "action": "log_weight",
            "description": "Log weight reading"
        }
        response = await ac.post("/api/v1/commands", json=command_data)
        assert response.status_code == 201
        
        # Process voice command
        process_data = {"command": "log my weight as 70 kilograms"}
        response = await ac.post("/api/v1/nlp/commands", json=process_data)
        assert response.status_code == 200
        assert response.json()["action"] == "log_weight"
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "voice-input-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "models_loaded": True
    }
```

### Metrics
- **Transcription Accuracy**: Word error rate and confidence scores
- **Processing Latency**: Time to process audio files
- **Real-time Performance**: WebSocket connection metrics
- **Storage Usage**: Audio file storage and database usage
- **Model Performance**: NLP model accuracy and response times

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/speech/transcribe")
async def transcribe_audio(audio_file: UploadFile, current_user: User = Depends(get_current_user)):
    logger.info(f"Audio transcription requested by user: {current_user.id}")
    # ... transcription logic
    logger.info(f"Transcription completed: {transcription_id}")
```

## Troubleshooting

### Common Issues

#### 1. Audio Quality Problems
**Symptoms**: Poor transcription accuracy
**Solution**: Implement audio preprocessing and noise reduction

#### 2. Model Loading Issues
**Symptoms**: Service startup failures
**Solution**: Verify model files and dependencies

#### 3. Memory Usage
**Symptoms**: High memory consumption
**Solution**: Optimize model loading and implement cleanup

#### 4. Real-time Performance
**Symptoms**: WebSocket connection issues
**Solution**: Optimize streaming and implement connection pooling

### Performance Optimization
- **Model Caching**: Cache loaded models in memory
- **Batch Processing**: Process multiple audio files in batches
- **Audio Compression**: Compress audio before processing
- **Connection Pooling**: Optimize WebSocket connections

### Security Considerations
1. **Audio Data Privacy**: Encrypt stored audio files
2. **Voice Biometrics Security**: Secure voice profile storage
3. **Input Validation**: Validate all audio inputs
4. **Access Control**: Implement proper authorization
5. **Data Retention**: Implement audio data retention policies

---

## Conclusion

The Voice Input Service provides comprehensive speech-to-text and natural language processing capabilities for the Personal Health Assistant platform. With advanced audio processing, real-time transcription, and voice command interpretation, it enables intuitive voice-based interactions for users.

For additional support or questions, please refer to the platform documentation or contact the development team. 