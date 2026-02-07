#!/usr/bin/env python3
"""
Basic test for Voice Input Service without external dependencies
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

def test_basic_imports():
    """Test basic imports without external dependencies"""
    print("🧪 Testing basic imports...")
    
    try:
        # Test basic imports
        from models.voice_input import VoiceInputCreate, InputType
        print("✅ Voice input models imported successfully")
        
        from services.voice_processing_service import VoiceProcessingService
        print("✅ Voice processing service imported successfully")
        
        print("🎉 All basic imports work!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_service():
    """Test basic service functionality"""
    print("\n🧪 Testing basic service functionality...")
    
    try:
        from services.voice_processing_service import VoiceProcessingService
        
        # Initialize service
        service = VoiceProcessingService()
        print("✅ Service initialized successfully")
        
        # Test basic method
        result = service.validate_audio_file("/tmp/test.wav")
        print(f"✅ Validation method works: {result}")
        
        print("🎉 Basic service functionality works!")
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting basic tests...")
    
    success1 = test_basic_imports()
    success2 = test_basic_service()
    
    if success1 and success2:
        print("\n🎉 All basic tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 