# Vision Analysis Service

## Overview

The Vision Analysis Service is a comprehensive solution for vision-enabled voice input processing that allows users to:

1. **Upload images** (medical conditions, symptoms, etc.)
2. **Ask questions via voice or text** about the image
3. **Get AI-powered analysis** using GROQ or OpenAI vision models
4. **Receive audio responses** through text-to-speech conversion

This service is particularly useful for medical applications where patients can take photos of symptoms and get immediate AI-powered analysis with voice responses.

## Features

### 🖼️ Image Processing
- Support for multiple image formats (JPEG, PNG, WebP, TIFF, BMP)
- Automatic image validation and optimization
- Patient-specific image storage and organization

### 🎤 Speech-to-Text
- High-quality transcription using OpenAI Whisper
- Support for multiple languages
- Audio enhancement and noise reduction

### 🤖 Vision Model Integration
- **GROQ Integration**: Fast inference with LLaVA models
  - `llava-3.1-8b-instant` (recommended for speed)
  - `llava-3.1-8b`
  - `llava-3.1-70b`
- **OpenAI Integration**: High-quality analysis with GPT models
  - `gpt-4-vision-preview`
  - `gpt-4o`
  - `gpt-4o-mini`

### 🔊 Text-to-Speech
- **Edge TTS**: Microsoft's neural voices
- **OpenAI TTS**: Advanced natural voices
- Multiple voice options and languages
- Audio format support (MP3, WAV, M4A, OGG, FLAC)

### 💰 Cost Tracking
- Real-time cost calculation for API usage
- Detailed cost breakdown by service
- Cost optimization recommendations

## API Endpoints

### 1. Complete Vision Voice Analysis
**POST** `/api/v1/voice-input/vision-analysis/complete-analysis`

Complete workflow endpoint that processes:
1. Image upload
2. Speech-to-text conversion (if voice query provided)
3. Vision model analysis
4. Text-to-speech response generation

**Parameters:**
- `patient_id` (UUID, required): Patient identifier
- `session_id` (string, optional): Session identifier
- `image_file` (file, optional): Image file to analyze
- `voice_query_file` (file, optional): Voice query audio file
- `text_query` (string, optional): Text query (alternative to voice)
- `vision_provider` (string, default: "groq"): "groq" or "openai"
- `vision_model` (string, default: "llava-3.1-8b-instant"): Model to use
- `tts_provider` (string, default: "edge_tts"): TTS provider
- `tts_voice` (string, default: "en-US-JennyNeural"): Voice to use
- `audio_output_format` (string, default: "mp3"): Output audio format

**Example Request:**
```bash
curl -X POST "http://localhost:8010/api/v1/voice-input/vision-analysis/complete-analysis" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "image_file=@rash_photo.jpg" \
  -F "text_query=What medical condition might this image show?" \
  -F "vision_provider=groq" \
  -F "vision_model=llava-3.1-8b-instant" \
  -F "tts_provider=edge_tts" \
  -F "tts_voice=en-US-JennyNeural" \
  -F "audio_output_format=mp3"
```

### 2. Image Upload
**POST** `/api/v1/voice-input/vision-analysis/upload-image`

Upload an image for analysis.

**Parameters:**
- `patient_id` (UUID, required): Patient identifier
- `image_file` (file, required): Image file
- `session_id` (string, optional): Session identifier

### 3. Speech-to-Text
**POST** `/api/v1/voice-input/vision-analysis/speech-to-text`

Convert speech to text using Whisper.

**Parameters:**
- `audio_file` (file, required): Audio file
- `language` (string, default: "en"): Language code
- `model` (string, default: "whisper-1"): Whisper model
- `enhance_audio` (boolean, default: true): Audio enhancement

### 4. Vision Analysis
**POST** `/api/v1/voice-input/vision-analysis/analyze-vision`

Analyze image with vision model.

**Parameters:**
- `image_file` (file, required): Image file
- `query` (string, required): Text query
- `provider` (string, default: "groq"): "groq" or "openai"
- `model` (string, default: "llava-3.1-8b-instant"): Model to use
- `max_tokens` (integer, default: 1000): Maximum response tokens
- `temperature` (float, default: 0.7): Response temperature

### 5. Text-to-Speech
**POST** `/api/v1/voice-input/vision-analysis/text-to-speech`

Convert text to speech.

**Parameters:**
- `text` (string, required): Text to convert
- `provider` (string, default: "edge_tts"): TTS provider
- `voice` (string, default: "en-US-JennyNeural"): Voice to use
- `language` (string, default: "en-US"): Language code
- `audio_format` (string, default: "mp3"): Output format
- `speed` (float, default: 1.0): Speech speed
- `pitch` (float, default: 1.0): Speech pitch
- `volume` (float, default: 1.0): Speech volume

### 6. Get Audio File
**GET** `/api/v1/voice-input/vision-analysis/audio/{tts_id}`

Retrieve generated audio file.

### 7. Get Image File
**GET** `/api/v1/voice-input/vision-analysis/image/{image_id}`

Retrieve uploaded image file.

### 8. Get Providers
**GET** `/api/v1/voice-input/vision-analysis/providers/vision`
**GET** `/api/v1/voice-input/vision-analysis/providers/tts`

Get available vision and TTS providers.

### 9. Get Formats
**GET** `/api/v1/voice-input/vision-analysis/formats/audio`
**GET** `/api/v1/voice-input/vision-analysis/formats/image`

Get supported audio and image formats.

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# API Keys
GROQ_API_KEY=${GROQ_API_KEY:-}
OPENAI_API_KEY=your_openai_api_key_here

# Service Configuration
HOST=0.0.0.0
PORT=8010
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_jwt_secret_key

# Vision Analysis Configuration
VISION_MODEL_DEFAULT=llava-3.1-8b-instant
TTS_PROVIDER_DEFAULT=edge_tts
TTS_VOICE_DEFAULT=en-US-JennyNeural
MAX_IMAGE_SIZE=10485760  # 10MB
```

### Docker Configuration

Add to your `docker-compose.yml`:

```yaml
voice-input-service:
  build:
    context: .
    dockerfile: apps/voice_input/Dockerfile
  ports:
    - "8010:8010"
  environment:
    - GROQ_API_KEY=${GROQ_API_KEY}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  volumes:
    - ./uploads:/app/uploads
    - ./outputs:/app/outputs
```

## Usage Examples

### Medical Scenario: Rash Analysis

```python
import requests

# Complete vision voice analysis for medical condition
def analyze_rash(image_path, patient_id):
    url = "http://localhost:8010/api/v1/voice-input/vision-analysis/complete-analysis"
    
    with open(image_path, 'rb') as f:
        files = {
            'image_file': ('rash.jpg', f, 'image/jpeg')
        }
        data = {
            'patient_id': patient_id,
            'text_query': 'I have this rash on my skin. What could it be? Is it serious?',
            'vision_provider': 'groq',
            'vision_model': 'llava-3.1-8b-instant',
            'tts_provider': 'edge_tts',
            'tts_voice': 'en-US-JennyNeural',
            'audio_output_format': 'mp3'
        }
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis: {result['vision_analysis']['response']}")
            print(f"Audio file: {result['text_to_speech']['audio_file_path']}")
            print(f"Cost: ${result['total_cost']:.4f}")
        else:
            print(f"Error: {response.text}")

# Usage
analyze_rash("rash_photo.jpg", "123e4567-e89b-12d3-a456-426614174000")
```

### Voice Query with Image

```python
import requests

# Voice query with image analysis
def voice_query_with_image(image_path, voice_path, patient_id):
    url = "http://localhost:8010/api/v1/voice-input/vision-analysis/complete-analysis"
    
    with open(image_path, 'rb') as img_file, open(voice_path, 'rb') as voice_file:
        files = {
            'image_file': ('image.jpg', img_file, 'image/jpeg'),
            'voice_query_file': ('query.wav', voice_file, 'audio/wav')
        }
        data = {
            'patient_id': patient_id,
            'vision_provider': 'openai',
            'vision_model': 'gpt-4-vision-preview',
            'tts_provider': 'openai_tts',
            'tts_voice': 'alloy'
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()
```

## Testing

Run the comprehensive test script:

```bash
cd apps/voice_input
python test_vision_analysis.py
```

This will test:
- All API endpoints
- Image upload functionality
- Speech-to-text conversion
- Vision model integration
- Text-to-speech synthesis
- Complete workflow
- Medical scenario simulation

## Cost Optimization

### GROQ vs OpenAI

**GROQ (Recommended for speed):**
- Faster inference (sub-second responses)
- Lower cost per token
- Good for real-time applications
- Models: LLaVA variants

**OpenAI (Recommended for quality):**
- Higher quality responses
- Better medical knowledge
- More detailed analysis
- Models: GPT-4 Vision variants

### Cost Tracking

The service tracks costs for:
- Vision model API calls
- Speech-to-text processing
- Text-to-speech synthesis

Example cost breakdown:
```json
{
  "total_cost": 0.0234,
  "cost_breakdown": {
    "vision_analysis": 0.0189,
    "text_to_speech": 0.0045
  }
}
```

## Security Considerations

1. **API Key Management**: Store API keys securely in environment variables
2. **Image Validation**: Validate image files to prevent malicious uploads
3. **Patient Data**: Ensure patient data is properly secured and anonymized
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Audit Logging**: Log all API calls for compliance and debugging

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure GROQ_API_KEY and OPENAI_API_KEY are set
   - Verify API keys are valid and have sufficient credits

2. **Image Upload Failures**
   - Check image format is supported
   - Ensure image size is under 10MB
   - Verify file permissions

3. **Vision Model Errors**
   - Check model availability
   - Verify API quotas and limits
   - Ensure proper image encoding

4. **Audio Generation Issues**
   - Check TTS provider availability
   - Verify voice selection
   - Ensure text is not empty

### Logs

Check service logs for detailed error information:

```bash
docker logs voice-input-service
```

## Integration with Other Services

The Vision Analysis Service integrates with:

- **Authentication Service**: User authentication and authorization
- **User Profile Service**: Patient profile management
- **Health Tracking Service**: Health data integration
- **Medical Records Service**: Medical record storage
- **AI Insights Service**: Advanced analytics

## Future Enhancements

1. **Multi-language Support**: Enhanced language detection and translation
2. **Batch Processing**: Process multiple images simultaneously
3. **Custom Models**: Support for custom vision models
4. **Real-time Streaming**: Live audio streaming capabilities
5. **Advanced Analytics**: Detailed usage analytics and insights
6. **Mobile Integration**: Native mobile app support
7. **WebRTC Support**: Real-time voice communication
8. **Offline Mode**: Local processing capabilities

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Test with the provided test script
4. Contact the development team

## License

This service is part of the Personal Health Assistant project and follows the same licensing terms. 