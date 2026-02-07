# Voice Input Service

A comprehensive multi-modal voice input processing service for the VitaSense Personal Health Assistant platform. This service handles voice input processing, transcription, text-to-speech synthesis, intent recognition, and multi-modal fusion.

## Features

### 🎤 Voice Processing
- Audio quality analysis and metrics
- Support for multiple audio formats (WAV, MP3, M4A, FLAC, OGG)
- Audio enhancement and noise reduction
- Format conversion and resampling

### 📝 Speech-to-Text Transcription
- High-accuracy transcription using Whisper
- Multi-language support (EN, ES, FR, DE, IT, PT, RU, ZH, JA, KO)
- Transcription enhancement and correction
- Language detection and translation
- Keyword extraction and batch processing

### 🔊 Text-to-Speech Synthesis
- Neural voice synthesis with multiple engines (Edge TTS, gTTS, pyttsx3)
- Multi-language support (EN-US, EN-GB, ES, FR, DE, IT, PT, RU, ZH, JA, KO)
- Emotional expression control (neutral, happy, sad, angry, excited, calm, concerned, professional)
- Prosody control (speech rate, pitch, volume)
- SSML markup support for advanced speech control
- Voice profile management with quality metrics

### 🧠 Intent Recognition
- Health-domain specific intent recognition
- Entity extraction (symptoms, medications, body parts)
- Sentiment analysis and urgency detection
- Context-aware processing

### 🔄 Multi-Modal Fusion
- Voice, text, image, and sensor data integration
- Multiple fusion strategies (early, late, hybrid)
- Health indicator extraction
- Intelligent recommendations

### 🔊 Audio Enhancement
- Noise reduction using spectral gating
- Audio normalization and filtering
- Dynamic range compression
- Quality comparison tools

## API Endpoints

### Voice Input Management
- `POST /api/v1/voice-input/upload` - Upload and process voice input
- `GET /api/v1/voice-input/{id}` - Get voice input by ID
- `GET /api/v1/voice-input/patient/{patient_id}` - Get patient's voice inputs
- `PUT /api/v1/voice-input/{id}` - Update voice input
- `DELETE /api/v1/voice-input/{id}` - Delete voice input

### Transcription
- `POST /api/v1/voice-input/transcription/transcribe` - Transcribe audio
- `POST /api/v1/voice-input/transcription/enhance` - Enhance transcription
- `POST /api/v1/voice-input/transcription/translate` - Translate transcription
- `POST /api/v1/voice-input/transcription/detect-language` - Detect language
- `POST /api/v1/voice-input/transcription/extract-keywords` - Extract keywords

### Text-to-Speech
- `POST /api/v1/voice-input/text-to-speech/synthesize` - Synthesize speech from text
- `POST /api/v1/voice-input/text-to-speech/synthesize-simple` - Simple synthesis with form data
- `GET /api/v1/voice-input/text-to-speech/audio/{synthesis_id}` - Get synthesized audio
- `GET /api/v1/voice-input/text-to-speech/voices` - Get available voices
- `GET /api/v1/voice-input/text-to-speech/voices/{voice_id}` - Get voice profile
- `POST /api/v1/voice-input/text-to-speech/batch-synthesize` - Batch synthesis
- `POST /api/v1/voice-input/text-to-speech/preview` - Generate speech preview
- `GET /api/v1/voice-input/text-to-speech/capabilities` - Get TTS capabilities
- `POST /api/v1/voice-input/text-to-speech/test-voice` - Test specific voice

### Intent Recognition
- `POST /api/v1/voice-input/intent/recognize` - Recognize intent from text
- `POST /api/v1/voice-input/intent/health-intent` - Extract health intent
- `POST /api/v1/voice-input/intent/analyze-sentiment` - Analyze sentiment
- `POST /api/v1/voice-input/intent/extract-entities` - Extract entities
- `POST /api/v1/voice-input/intent/determine-urgency` - Determine urgency

### Multi-Modal Processing
- `POST /api/v1/voice-input/multi-modal/process` - Process multi-modal input
- `POST /api/v1/voice-input/multi-modal/voice-text` - Process voice and text
- `POST /api/v1/voice-input/multi-modal/voice-sensor` - Process voice and sensor data
- `POST /api/v1/voice-input/multi-modal/text-sensor` - Process text and sensor data

### Audio Enhancement
- `POST /api/v1/voice-input/audio-enhancement/enhance` - Enhance audio quality
- `POST /api/v1/voice-input/audio-enhancement/batch-enhance` - Batch enhance audio
- `POST /api/v1/voice-input/audio-enhancement/compare` - Compare audio quality
- `POST /api/v1/voice-input/audio-enhancement/convert-format` - Convert audio format

## Quick Start

### Prerequisites
- Python 3.11+
- FFmpeg
- PostgreSQL (for production)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PersonalHealthAssistant/apps/voice_input
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

4. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/voice_input_db"
export SECRET_KEY="your-secret-key"
```

5. Run the service:
```bash
python main.py
```

The service will be available at `http://localhost:8004`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t voice-input-service .
```

2. Run the container:
```bash
docker run -p 8004:8004 voice-input-service
```

## Usage Examples

### Upload Voice Input
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "input_type=voice_command" \
  -F "audio_file=@voice_input.wav"
```

### Transcribe Audio
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/transcription/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@audio.wav" \
  -F "language=en"
```

### Synthesize Speech
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/text-to-speech/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I am your health assistant. How can I help you today?",
    "voice_id": "en-US-Neural2-F",
    "language": "en-US",
    "emotion": "professional",
    "speech_rate": "normal",
    "pitch_level": "normal",
    "volume": 1.0
  }'
```

### Simple Speech Synthesis
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/text-to-speech/synthesize-simple" \
  -H "Content-Type: multipart/form-data" \
  -F "text=This is a test of the text-to-speech system" \
  -F "voice_id=en-US-Neural2-F" \
  -F "emotion=neutral"
```

### Recognize Intent
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/intent/recognize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I have a severe headache",
    "voice_input_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### Process Multi-Modal Input
```bash
curl -X POST "http://localhost:8004/api/v1/voice-input/multi-modal/process" \
  -H "Content-Type: multipart/form-data" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "text_input=I have chest pain" \
  -F "voice_file=@voice.wav" \
  -F "sensor_data=[{\"sensor_type\":\"heart_rate\",\"sensor_value\":120,\"unit\":\"bpm\"}]"
```

## Text-to-Speech Features

### Voice Profiles
- **Emma (Neural)**: Professional female voice with American accent
- **James (Neural)**: Professional male voice with American accent  
- **Sophie (Neural)**: Professional female voice with British accent

### Emotional Expressions
- **Neutral**: Standard professional tone
- **Happy**: Upbeat and positive
- **Sad**: Softer and more subdued
- **Angry**: Stronger and more intense
- **Excited**: Energetic and enthusiastic
- **Calm**: Relaxed and soothing
- **Concerned**: Caring and empathetic
- **Professional**: Clear and authoritative

### Speech Control
- **Speech Rate**: Very slow, slow, normal, fast, very fast
- **Pitch Level**: Very low, low, normal, high, very high
- **Volume**: 0.0 to 2.0 (0.0 = silent, 1.0 = normal, 2.0 = maximum)

### SSML Support
```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-Neural2-F">
        <prosody rate="medium" pitch="medium" volume="1.0">
            Hello, this is a test of SSML markup.
            <break time="1s"/>
            I can control speech rate, pitch, and volume.
        </prosody>
    </voice>
</speak>
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_AUDIO_DURATION`: Maximum audio duration in seconds (default: 300)
- `SUPPORTED_AUDIO_FORMATS`: Comma-separated list of supported audio formats

### Audio Processing Settings
- Maximum audio duration: 5 minutes
- Supported formats: WAV, MP3, M4A, FLAC, OGG
- Default sample rate: 16kHz
- Default channels: Mono

### Text-to-Speech Settings
- Supported languages: EN-US, EN-GB, ES, FR, DE, IT, PT, RU, ZH, JA, KO
- Voice types: Neural, Concatenative, HMM, DNN, WaveNet, Tacotron
- Default sample rate: 22.05kHz
- SSML support: Enabled by default

## Architecture

### Services
- **VoiceProcessingService**: Handles audio quality analysis and processing
- **TranscriptionService**: Manages speech-to-text conversion
- **TextToSpeechService**: Manages text-to-speech synthesis
- **IntentRecognitionService**: Recognizes user intentions and extracts entities
- **MultiModalService**: Combines multiple input modalities
- **AudioEnhancementService**: Enhances audio quality

### Models
- **VoiceInput**: Core voice input data model
- **TranscriptionResult**: Speech-to-text results
- **TextToSpeechResult**: Text-to-speech results
- **VoiceProfile**: Voice characteristics and capabilities
- **IntentRecognitionResult**: Intent recognition results
- **MultiModalResult**: Multi-modal processing results
- **AudioEnhancementResult**: Audio enhancement results

## Health Domain Features

### Intent Recognition
- Symptom reporting
- Medication queries
- Appointment requests
- Emergency alerts
- Wellness queries

### Entity Extraction
- Body parts
- Symptoms
- Medications
- Severity levels
- Time durations

### Health Indicators
- Heart rate
- Blood pressure
- Temperature
- Blood sugar levels

### Voice Interaction Workflow
1. **Voice Input**: User speaks health concern
2. **Processing**: Audio quality analysis and enhancement
3. **Transcription**: Convert speech to text
4. **Intent Recognition**: Understand user's intent
5. **Response Generation**: Generate appropriate response
6. **Text-to-Speech**: Convert response to speech
7. **Audio Output**: Deliver synthesized response

## Performance

### Benchmarks
- Audio processing: ~2-5 seconds per minute of audio
- Transcription: ~1-3 seconds per minute of audio
- Text-to-speech: ~0.5-2 seconds per sentence
- Intent recognition: ~100-500ms per text
- Multi-modal fusion: ~1-2 seconds per input

### Scalability
- Horizontal scaling support
- Background task processing
- Batch processing capabilities
- Caching for repeated operations

## Monitoring

### Health Checks
- `/health` - Service health status
- `/ready` - Service readiness
- `/capabilities` - Service capabilities

### Metrics
- Processing time
- Success/failure rates
- Audio quality scores
- Intent recognition accuracy
- TTS quality metrics

## Security

### Authentication
- JWT token-based authentication
- Role-based access control
- API key validation

### Data Protection
- Audio file encryption
- Secure file storage
- Data anonymization
- HIPAA compliance features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 