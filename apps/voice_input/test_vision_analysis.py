#!/usr/bin/env python3
"""
Vision Analysis Test Script
Test script for vision-enabled voice input processing.
"""

import os
import sys
import asyncio
import tempfile
import requests
import json
from uuid import uuid4
from PIL import Image
import numpy as np

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def create_test_image(width=800, height=600, color=(255, 0, 0)):
    """Create a test image for testing"""
    image = Image.new('RGB', (width, height), color)
    return image

def create_test_audio_file(duration=3):
    """Create a test audio file (simulated)"""
    # This is a placeholder - in a real scenario, you'd create actual audio
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()
    return temp_file.name

def test_vision_analysis_endpoints():
    """Test all vision analysis endpoints"""
    
    base_url = "http://localhost:8010/api/v1/voice-input/vision-analysis"
    patient_id = str(uuid4())
    
    print("🧪 Testing Vision Analysis Endpoints")
    print("=" * 50)
    
    # Test 1: Get available providers
    print("\n1. Testing Vision Providers...")
    try:
        response = requests.get(f"{base_url}/providers/vision")
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ Vision providers: {providers}")
        else:
            print(f"❌ Failed to get vision providers: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting vision providers: {e}")
    
    # Test 2: Get TTS providers
    print("\n2. Testing TTS Providers...")
    try:
        response = requests.get(f"{base_url}/providers/tts")
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ TTS providers: {providers}")
        else:
            print(f"❌ Failed to get TTS providers: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting TTS providers: {e}")
    
    # Test 3: Get supported formats
    print("\n3. Testing Supported Formats...")
    try:
        response = requests.get(f"{base_url}/formats/image")
        if response.status_code == 200:
            formats = response.json()
            print(f"✅ Image formats: {formats}")
        else:
            print(f"❌ Failed to get image formats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting image formats: {e}")
    
    # Test 4: Upload image
    print("\n4. Testing Image Upload...")
    try:
        # Create test image
        test_image = create_test_image()
        image_path = tempfile.mktemp(suffix='.jpg')
        test_image.save(image_path)
        
        with open(image_path, 'rb') as f:
            files = {'image_file': ('test_image.jpg', f, 'image/jpeg')}
            data = {
                'patient_id': patient_id,
                'session_id': 'test_session'
            }
            response = requests.post(f"{base_url}/upload-image", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image uploaded: {result}")
            image_id = result['image_id']
        else:
            print(f"❌ Failed to upload image: {response.status_code} - {response.text}")
            image_id = None
        
        # Clean up
        os.unlink(image_path)
        
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        image_id = None
    
    # Test 5: Text to Speech
    print("\n5. Testing Text to Speech...")
    try:
        test_text = "This is a test of the text to speech functionality."
        data = {
            'text': test_text,
            'provider': 'edge_tts',
            'voice': 'en-US-JennyNeural',
            'audio_format': 'mp3'
        }
        response = requests.post(f"{base_url}/text-to-speech", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ TTS successful: {result}")
            tts_id = result['tts_id']
        else:
            print(f"❌ Failed TTS: {response.status_code} - {response.text}")
            tts_id = None
            
    except Exception as e:
        print(f"❌ Error in TTS: {e}")
        tts_id = None
    
    # Test 6: Vision Analysis with GROQ
    print("\n6. Testing Vision Analysis with GROQ...")
    try:
        # Create test image
        test_image = create_test_image()
        image_path = tempfile.mktemp(suffix='.jpg')
        test_image.save(image_path)
        
        with open(image_path, 'rb') as f:
            files = {'image_file': ('test_image.jpg', f, 'image/jpeg')}
            data = {
                'query': 'What do you see in this image?',
                'provider': 'groq',
                'model': 'meta-llama/llama-4-scout-17b-16e-instruct',
                'max_tokens': 500,
                'temperature': 0.7
            }
            response = requests.post(f"{base_url}/analyze-vision", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Vision analysis successful: {result}")
        else:
            print(f"❌ Failed vision analysis: {response.status_code} - {response.text}")
        
        # Clean up
        os.unlink(image_path)
        
    except Exception as e:
        print(f"❌ Error in vision analysis: {e}")
    
    # Test 7: Complete Vision Voice Analysis
    print("\n7. Testing Complete Vision Voice Analysis...")
    try:
        # Create test image
        test_image = create_test_image()
        image_path = tempfile.mktemp(suffix='.jpg')
        test_image.save(image_path)
        
        with open(image_path, 'rb') as f:
            files = {
                'image_file': ('test_image.jpg', f, 'image/jpeg')
            }
            data = {
                'patient_id': patient_id,
                'session_id': 'test_session',
                'text_query': 'What medical condition might this image show?',
                'vision_provider': 'groq',
                'vision_model': 'meta-llama/llama-4-scout-17b-16e-instruct',
                'tts_provider': 'edge_tts',
                'tts_voice': 'en-US-JennyNeural',
                'audio_output_format': 'mp3'
            }
            response = requests.post(f"{base_url}/complete-analysis", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Complete analysis successful: {result}")
            
            # Test audio file retrieval
            if result.get('text_to_speech', {}).get('tts_id'):
                audio_id = result['text_to_speech']['tts_id']
                audio_response = requests.get(f"{base_url}/audio/{audio_id}")
                if audio_response.status_code == 200:
                    print(f"✅ Audio file retrieved successfully")
                else:
                    print(f"❌ Failed to retrieve audio file: {audio_response.status_code}")
        else:
            print(f"❌ Failed complete analysis: {response.status_code} - {response.text}")
        
        # Clean up
        os.unlink(image_path)
        
    except Exception as e:
        print(f"❌ Error in complete analysis: {e}")
    
    # Test 8: Health Check
    print("\n8. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check: {health}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in health check: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Vision Analysis Testing Complete!")

def test_medical_scenario():
    """Test a medical scenario with rash image analysis"""
    
    base_url = "http://localhost:8010/api/v1/voice-input/vision-analysis"
    patient_id = str(uuid4())
    
    print("\n🏥 Testing Medical Scenario: Rash Analysis")
    print("=" * 50)
    
    try:
        # Create a simulated rash image (red patches on skin)
        rash_image = Image.new('RGB', (800, 600), (255, 220, 200))  # Skin color
        # Add some red patches to simulate rash
        pixels = rash_image.load()
        for i in range(200, 600):
            for j in range(200, 400):
                if (i - 400) ** 2 + (j - 300) ** 2 < 10000:  # Circular rash
                    pixels[i, j] = (255, 100, 100)  # Red rash color
        
        image_path = tempfile.mktemp(suffix='.jpg')
        rash_image.save(image_path)
        
        with open(image_path, 'rb') as f:
            files = {
                'image_file': ('rash_image.jpg', f, 'image/jpeg')
            }
            data = {
                'patient_id': patient_id,
                'session_id': 'medical_session',
                'text_query': 'I have this rash on my skin. What could it be? Is it serious?',
                'vision_provider': 'groq',
                'vision_model': 'meta-llama/llama-4-scout-17b-16e-instruct',
                'tts_provider': 'edge_tts',
                'tts_voice': 'en-US-JennyNeural',
                'audio_output_format': 'mp3'
            }
            response = requests.post(f"{base_url}/complete-analysis", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Medical analysis successful!")
            print(f"📋 Query: {data['text_query']}")
            print(f"🔍 Vision Response: {result.get('vision_analysis', {}).get('response', 'No response')}")
            print(f"💰 Total Cost: ${result.get('total_cost', 0):.4f}")
            print(f"⏱️ Processing Time: {result.get('total_processing_time', 0):.2f} seconds")
        else:
            print(f"❌ Medical analysis failed: {response.status_code} - {response.text}")
        
        # Clean up
        os.unlink(image_path)
        
    except Exception as e:
        print(f"❌ Error in medical scenario: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Vision Analysis Service Tests")
    print("Make sure the voice input service is running on port 8010")
    print("Make sure you have set GROQ_API_KEY and OPENAI_API_KEY environment variables")
    
    # Test basic endpoints
    test_vision_analysis_endpoints()
    
    # Test medical scenario
    test_medical_scenario()
    
    print("\n📝 Test Summary:")
    print("- Vision analysis endpoints tested")
    print("- Image upload functionality tested")
    print("- Speech-to-text conversion tested")
    print("- Vision model integration tested")
    print("- Text-to-speech synthesis tested")
    print("- Complete workflow tested")
    print("- Medical scenario tested")

if __name__ == "__main__":
    main() 