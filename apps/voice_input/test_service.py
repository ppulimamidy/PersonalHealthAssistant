#!/usr/bin/env python3
"""
Test script for Voice Input Service
Tests the main functionality of the voice input service.
"""

import asyncio
import json
import tempfile
import wave
import struct
import math
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from apps.voice_input.services.voice_processing_service import VoiceProcessingService
from apps.voice_input.services.transcription_service import TranscriptionService
from apps.voice_input.services.intent_recognition_service import IntentRecognitionService
from apps.voice_input.services.multi_modal_service import MultiModalService
from apps.voice_input.services.audio_enhancement_service import AudioEnhancementService
from apps.voice_input.services.text_to_speech_service import TextToSpeechService
from apps.voice_input.models.multi_modal import MultiModalInput, TextInput, SensorInput
from apps.voice_input.models.text_to_speech import TextToSpeechRequest, EmotionType, SpeechRate, PitchLevel
from common.utils.logging import get_logger

logger = get_logger(__name__)


def create_test_audio_file(duration_seconds=3, frequency=440):
    """Create a test audio file with a sine wave."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file_path = temp_file.name
    temp_file.close()
    
    # Audio parameters
    sample_rate = 16000
    num_samples = int(duration_seconds * sample_rate)
    
    # Create sine wave
    with wave.open(temp_file_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        frames = []
        for i in range(num_samples):
            # Generate sine wave
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            frames.append(sample)
        
        # Write frames
        frame_data = struct.pack('h' * len(frames), *frames)
        wav_file.writeframes(frame_data)
    
    return temp_file_path


async def test_voice_processing_service():
    """Test the voice processing service."""
    print("🧪 Testing Voice Processing Service...")
    
    try:
        service = VoiceProcessingService()
        
        # Create test audio file
        audio_file = create_test_audio_file(3, 440)
        
        # Process voice input
        result = await service.process_voice_input(audio_file, "test-id")
        
        print(f"✅ Voice processing successful:")
        print(f"   - Audio duration: {result.audio_duration:.2f}s")
        print(f"   - Audio format: {result.audio_format}")
        print(f"   - Quality score: {result.audio_quality_score:.2f}")
        print(f"   - Processing time: {result.processing_time:.2f}s")
        
        # Clean up
        os.unlink(audio_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Voice processing failed: {str(e)}")
        return False


async def test_transcription_service():
    """Test the transcription service."""
    print("\n🧪 Testing Transcription Service...")
    
    try:
        service = TranscriptionService()
        
        # Create test audio file
        audio_file = create_test_audio_file(3, 440)
        
        # Transcribe audio
        result = await service.transcribe_audio(audio_file, "test-id")
        
        print(f"✅ Transcription successful:")
        print(f"   - Full text: '{result.full_text}'")
        print(f"   - Confidence: {result.overall_confidence:.2f}")
        print(f"   - Language: {result.detected_language}")
        print(f"   - Processing time: {result.processing_time:.2f}s")
        
        # Clean up
        os.unlink(audio_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        return False


async def test_text_to_speech_service():
    """Test the text-to-speech service."""
    print("\n🧪 Testing Text-to-Speech Service...")
    
    try:
        service = TextToSpeechService()
        
        # Test basic synthesis
        request = TextToSpeechRequest(
            text="Hello, this is a test of the text-to-speech system.",
            voice_id="en-US-Neural2-F",
            language="en-US",
            emotion=EmotionType.NEUTRAL,
            speech_rate=SpeechRate.NORMAL,
            pitch_level=PitchLevel.NORMAL,
            volume=1.0
        )
        
        result = await service.synthesize_speech(request)
        
        print(f"✅ Text-to-speech synthesis successful:")
        print(f"   - Synthesis ID: {result.synthesis_id}")
        print(f"   - Voice: {result.voice_name}")
        print(f"   - Audio duration: {result.audio_duration:.2f}s")
        print(f"   - Quality score: {result.quality_score:.2f}")
        print(f"   - Naturalness: {result.naturalness_score:.2f}")
        print(f"   - Intelligibility: {result.intelligibility_score:.2f}")
        print(f"   - Processing time: {result.processing_time:.2f}s")
        
        # Test emotion synthesis
        emotion_request = TextToSpeechRequest(
            text="I'm very excited about this new feature!",
            voice_id="en-US-Neural2-F",
            language="en-US",
            emotion=EmotionType.EXCITED,
            speech_rate=SpeechRate.FAST,
            pitch_level=PitchLevel.HIGH,
            volume=1.2
        )
        
        emotion_result = await service.synthesize_speech(emotion_request)
        
        print(f"✅ Emotional synthesis successful:")
        print(f"   - Emotion: {emotion_result.emotion}")
        print(f"   - Speech rate: {emotion_result.speech_rate}")
        print(f"   - Pitch level: {emotion_result.pitch_level}")
        
        # Get available voices
        voices = await service.get_available_voices()
        print(f"✅ Available voices: {len(voices)} voices found")
        
        return True
        
    except Exception as e:
        print(f"❌ Text-to-speech failed: {str(e)}")
        return False


async def test_intent_recognition_service():
    """Test the intent recognition service."""
    print("\n🧪 Testing Intent Recognition Service...")
    
    try:
        service = IntentRecognitionService()
        
        # Test text
        test_text = "I have a severe headache and need to see a doctor"
        
        # Recognize intent
        result = await service.recognize_intent(test_text, "test-id")
        
        print(f"✅ Intent recognition successful:")
        print(f"   - Primary intent: {result.primary_intent.intent_name}")
        print(f"   - Confidence: {result.primary_intent.confidence:.2f}")
        print(f"   - Priority: {result.primary_intent.priority}")
        print(f"   - Urgency level: {result.urgency_level}")
        print(f"   - Entities found: {len(result.entities)}")
        
        # Extract health intent
        health_intent = await service.extract_health_intent(test_text)
        
        print(f"   - Health intent: {health_intent.primary_health_intent}")
        print(f"   - Symptoms: {health_intent.symptoms}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intent recognition failed: {str(e)}")
        return False


async def test_multi_modal_service():
    """Test the multi-modal service."""
    print("\n🧪 Testing Multi-Modal Service...")
    
    try:
        service = MultiModalService()
        
        # Create multi-modal input
        multi_modal_input = MultiModalInput(
            patient_id="test-patient-123",
            session_id="test-session-456",
            text_input=TextInput(
                text_content="I have chest pain and my heart rate is elevated",
                language="en",
                source="test"
            ),
            sensor_inputs=[
                SensorInput(
                    sensor_type="heart_rate",
                    sensor_value=120,
                    unit="bpm",
                    device_id="test-device",
                    location="wrist"
                ),
                SensorInput(
                    sensor_type="blood_pressure",
                    sensor_value={"systolic": 140, "diastolic": 90},
                    unit="mmHg",
                    device_id="test-device",
                    location="arm"
                )
            ],
            priority=3,
            urgency_level=4
        )
        
        # Process multi-modal input
        result = await service.process_multi_modal_input(multi_modal_input)
        
        print(f"✅ Multi-modal processing successful:")
        print(f"   - Combined text: '{result.combined_text}'")
        print(f"   - Primary intent: {result.primary_intent}")
        print(f"   - Confidence score: {result.confidence_score:.2f}")
        print(f"   - Health indicators: {len(result.health_indicators)}")
        print(f"   - Recommendations: {len(result.recommendations)}")
        print(f"   - Processing time: {result.processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-modal processing failed: {str(e)}")
        return False


async def test_audio_enhancement_service():
    """Test the audio enhancement service."""
    print("\n🧪 Testing Audio Enhancement Service...")
    
    try:
        service = AudioEnhancementService()
        
        # Create test audio file
        audio_file = create_test_audio_file(3, 440)
        
        # Enhance audio
        result = await service.enhance_audio(
            audio_file, 
            ["normalization", "noise_reduction"]
        )
        
        print(f"✅ Audio enhancement successful:")
        print(f"   - Original path: {result.original_audio_path}")
        print(f"   - Enhanced path: {result.enhanced_audio_path}")
        print(f"   - Enhancements applied: {result.enhancement_applied}")
        print(f"   - Improvement score: {result.improvement_score:.2f}")
        print(f"   - Processing time: {result.processing_time:.2f}s")
        
        # Clean up
        os.unlink(audio_file)
        if result.enhanced_audio_path and os.path.exists(result.enhanced_audio_path):
            os.unlink(result.enhanced_audio_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Audio enhancement failed: {str(e)}")
        return False


async def test_voice_interaction_workflow():
    """Test a complete voice interaction workflow."""
    print("\n🧪 Testing Complete Voice Interaction Workflow...")
    
    try:
        # Initialize services
        voice_processor = VoiceProcessingService()
        transcription_service = TranscriptionService()
        tts_service = TextToSpeechService()
        intent_service = IntentRecognitionService()
        
        # Step 1: Create test audio (simulating user input)
        audio_file = create_test_audio_file(3, 440)
        
        # Step 2: Process voice input
        voice_result = await voice_processor.process_voice_input(audio_file, "workflow-test")
        print(f"✅ Step 1 - Voice processing: Quality score {voice_result.audio_quality_score:.2f}")
        
        # Step 3: Transcribe audio
        transcription_result = await transcription_service.transcribe_audio(audio_file, "workflow-test")
        print(f"✅ Step 2 - Transcription: '{transcription_result.full_text}'")
        
        # Step 4: Recognize intent
        intent_result = await intent_service.recognize_intent(
            transcription_result.full_text or "I need help with my health",
            "workflow-test"
        )
        print(f"✅ Step 3 - Intent recognition: {intent_result.primary_intent.intent_name}")
        
        # Step 5: Generate response using TTS
        response_text = f"I understand you need help. Let me assist you with {intent_result.primary_intent.intent_name}."
        
        tts_request = TextToSpeechRequest(
            text=response_text,
            voice_id="en-US-Neural2-F",
            language="en-US",
            emotion=EmotionType.PROFESSIONAL,
            speech_rate=SpeechRate.NORMAL,
            pitch_level=PitchLevel.NORMAL,
            volume=1.0
        )
        
        tts_result = await tts_service.synthesize_speech(tts_request)
        print(f"✅ Step 4 - Text-to-speech: Generated {tts_result.audio_duration:.2f}s of audio")
        
        # Clean up
        os.unlink(audio_file)
        
        print(f"✅ Complete workflow successful!")
        print(f"   - Total processing time: {voice_result.processing_time + transcription_result.processing_time + tts_result.processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice interaction workflow failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Voice Input Service Tests...\n")
    
    tests = [
        ("Voice Processing", test_voice_processing_service),
        ("Transcription", test_transcription_service),
        ("Text-to-Speech", test_text_to_speech_service),
        ("Intent Recognition", test_intent_recognition_service),
        ("Multi-Modal Processing", test_multi_modal_service),
        ("Audio Enhancement", test_audio_enhancement_service),
        ("Voice Interaction Workflow", test_voice_interaction_workflow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print("="*50)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 