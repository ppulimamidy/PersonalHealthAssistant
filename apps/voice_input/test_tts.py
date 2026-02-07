#!/usr/bin/env python3
"""
Simple test script for Text-to-Speech service
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from models.text_to_speech import TextToSpeechRequest, EmotionType, SpeechRate, PitchLevel, VoiceType
from services.text_to_speech_service import TextToSpeechService


async def test_tts_service():
    """Test the Text-to-Speech service"""
    print("🧪 Testing Text-to-Speech Service...")
    
    try:
        # Initialize service
        tts_service = TextToSpeechService()
        print("✅ TTS Service initialized successfully")
        
        # Test 1: Simple synthesis
        print("\n📝 Test 1: Simple text synthesis")
        request = TextToSpeechRequest(
            text="Hello, this is a test of the text-to-speech system.",
            voice_id="en-US-Neural2-F",
            language="en",
            emotion=EmotionType.NEUTRAL,
            speech_rate=SpeechRate.NORMAL,
            pitch_level=PitchLevel.NORMAL,
            volume=1.0
        )
        
        result = await tts_service.synthesize_speech(request)
        print(f"✅ Synthesis completed: {result.synthesis_successful}")
        print(f"   Audio file: {result.audio_file_path}")
        print(f"   Duration: {result.audio_duration}s")
        print(f"   Quality score: {result.quality_score}")
        
        # Test 2: Get available voices
        print("\n🎤 Test 2: Get available voices")
        voices = await tts_service.get_available_voices()
        print(f"✅ Found {len(voices)} available voices")
        for voice in voices[:3]:  # Show first 3
            print(f"   - {voice.voice_name} ({voice.voice_id})")
        
        # Test 3: Get specific voice profile
        print("\n👤 Test 3: Get voice profile")
        voice_profile = await tts_service.get_voice_profile("en-US-Neural2-F")
        if voice_profile:
            print(f"✅ Voice profile: {voice_profile.voice_name}")
            print(f"   Language: {voice_profile.language}")
            print(f"   Gender: {voice_profile.gender}")
            print(f"   Quality: {voice_profile.quality_metrics}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tts_service())
    sys.exit(0 if success else 1) 