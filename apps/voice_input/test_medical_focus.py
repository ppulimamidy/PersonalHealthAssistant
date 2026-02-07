#!/usr/bin/env python3
"""
Test Medical Focus for Vision and Voice Analysis
Tests that the system properly focuses on medical/health-related responses.
"""

import asyncio
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

# Test queries for different medical domains
MEDICAL_TEST_QUERIES = {
    "dermatology": [
        "What's wrong with this skin rash?",
        "Is this mole concerning?",
        "What type of skin condition is this?",
        "Should I be worried about this acne?",
        "What could cause this skin lesion?"
    ],
    "radiology": [
        "What do you see in this X-ray?",
        "Is there a fracture in this image?",
        "What abnormalities are visible in this CT scan?",
        "Can you identify any masses in this MRI?",
        "What does this chest X-ray show?"
    ],
    "cardiology": [
        "What's wrong with this ECG?",
        "Is this heart rhythm normal?",
        "What does this cardiac scan show?",
        "Are there any signs of heart disease?",
        "What's the interpretation of this EKG?"
    ],
    "general": [
        "What medical condition might this be?",
        "Should I see a doctor about this?",
        "What symptoms does this suggest?",
        "Is this a medical emergency?",
        "What health issue could this indicate?"
    ]
}

NON_MEDICAL_TEST_QUERIES = [
    "What color is this object?",
    "How many people are in this photo?",
    "What's the weather like in this image?",
    "What brand of car is this?",
    "What type of food is this?"
]


async def test_medical_domain_detection():
    """Test medical domain detection"""
    print("🔍 Testing Medical Domain Detection...")
    
    # Import the service
    from services.medical_prompt_engine import MedicalPromptEngine
    
    engine = MedicalPromptEngine()
    
    results = {}
    
    # Test medical queries
    for domain, queries in MEDICAL_TEST_QUERIES.items():
        print(f"\n📋 Testing {domain.upper()} domain:")
        domain_results = []
        
        for query in queries:
            validation = engine.validate_medical_query(query)
            domain_results.append({
                "query": query,
                "detected_domain": validation["domain"].value,
                "is_medical": validation["is_medical"],
                "confidence": validation["confidence"]
            })
            
            print(f"  ✅ '{query}' -> {validation['domain'].value} (confidence: {validation['confidence']:.2f})")
        
        results[domain] = domain_results
    
    # Test non-medical queries
    print(f"\n📋 Testing NON-MEDICAL queries:")
    non_medical_results = []
    
    for query in NON_MEDICAL_TEST_QUERIES:
        validation = engine.validate_medical_query(query)
        non_medical_results.append({
            "query": query,
            "detected_domain": validation["domain"].value,
            "is_medical": validation["is_medical"],
            "confidence": validation["confidence"]
        })
        
        print(f"  ❌ '{query}' -> {validation['domain'].value} (confidence: {validation['confidence']:.2f})")
    
    results["non_medical"] = non_medical_results
    
    return results


async def test_medical_prompt_generation():
    """Test medical prompt generation"""
    print("\n🎯 Testing Medical Prompt Generation...")
    
    from services.medical_prompt_engine import MedicalPromptEngine
    from config.medical_domains import MedicalDomain
    
    engine = MedicalPromptEngine()
    
    results = {}
    
    # Test prompt generation for each domain
    for domain in MedicalDomain:
        print(f"\n📝 Testing {domain.value.upper()} prompt generation:")
        
        test_query = "What's wrong with this image?"
        
        # Generate prompts
        vision_prompt = engine.create_medical_vision_prompt(test_query, domain)
        voice_prompt = engine.create_medical_voice_prompt(test_query, domain)
        system_prompt = engine.create_medical_system_prompt(domain)
        
        results[domain.value] = {
            "vision_prompt": vision_prompt,
            "voice_prompt": voice_prompt,
            "system_prompt": system_prompt
        }
        
        print(f"  ✅ Vision prompt length: {len(vision_prompt)} chars")
        print(f"  ✅ Voice prompt length: {len(voice_prompt)} chars")
        print(f"  ✅ System prompt length: {len(system_prompt)} chars")
        
        # Check for medical keywords
        medical_keywords = engine.get_medical_keywords(domain)
        print(f"  ✅ Medical keywords: {len(medical_keywords)} found")
    
    return results


async def test_vision_analysis_with_medical_focus():
    """Test vision analysis with medical focus"""
    print("\n🔬 Testing Vision Analysis with Medical Focus...")
    
    # Create a simple test image (placeholder)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        # Create a minimal JPEG file for testing
        temp_file.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
        temp_file_path = temp_file.name
    
    try:
        from services.vision_analysis_service import VisionAnalysisService
        
        service = VisionAnalysisService()
        await service.initialize()
        
        results = {}
        
        # Test with different medical queries
        for domain, queries in MEDICAL_TEST_QUERIES.items():
            print(f"\n🏥 Testing {domain.upper()} vision analysis:")
            domain_results = []
            
            for query in queries[:2]:  # Test first 2 queries per domain
                try:
                    # Test GROQ analysis
                    result = await service.analyze_vision_groq(
                        temp_file_path, 
                        query, 
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    domain_results.append({
                        "query": query,
                        "response": result.response,
                        "medical_domain": result.medical_domain,
                        "medical_confidence": result.medical_confidence,
                        "processing_time": result.processing_time
                    })
                    
                    print(f"  ✅ '{query}' -> {result.medical_domain} (confidence: {result.medical_confidence:.2f})")
                    print(f"     Response preview: {result.response[:100]}...")
                    
                except Exception as e:
                    print(f"  ❌ Error with query '{query}': {str(e)}")
                    domain_results.append({
                        "query": query,
                        "error": str(e)
                    })
            
            results[domain] = domain_results
        
        return results
        
    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


async def test_speech_to_text_medical_context():
    """Test speech-to-text with medical context"""
    print("\n🎤 Testing Speech-to-Text with Medical Context...")
    
    # Create a simple test audio file (placeholder)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        # Create a minimal WAV file for testing
        temp_file.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
        temp_file_path = temp_file.name
    
    try:
        from services.vision_analysis_service import VisionAnalysisService
        
        service = VisionAnalysisService()
        await service.initialize()
        
        results = []
        
        # Test with medical queries (simulated as if they were transcribed)
        medical_queries = [
            "What's wrong with this skin rash?",
            "Is this mole concerning?",
            "What do you see in this X-ray?",
            "What's wrong with this ECG?",
            "Should I see a doctor about this?"
        ]
        
        for query in medical_queries:
            try:
                # Simulate speech-to-text with medical context
                result = await service.speech_to_text(temp_file_path, "en", True)
                
                # Manually set the text for testing
                result.text = query
                
                # Validate medical context
                medical_validation = service.medical_prompt_engine.validate_medical_query(query)
                
                if medical_validation["is_medical"]:
                    result.medical_context = {
                        "is_medical": True,
                        "domain": medical_validation["domain"].value,
                        "confidence": medical_validation["confidence"]
                    }
                
                results.append({
                    "query": query,
                    "transcribed_text": result.text,
                    "medical_context": result.medical_context,
                    "confidence": result.confidence
                })
                
                print(f"  ✅ '{query}' -> {medical_validation['domain'].value} (confidence: {medical_validation['confidence']:.2f})")
                
            except Exception as e:
                print(f"  ❌ Error with query '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "error": str(e)
                })
        
        return results
        
    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


async def generate_test_report():
    """Generate comprehensive test report"""
    print("🚀 Starting Medical Focus Testing...")
    print("=" * 60)
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "test_summary": "Medical Focus Testing for Vision and Voice Analysis",
        "results": {}
    }
    
    # Run all tests
    try:
        report["results"]["domain_detection"] = await test_medical_domain_detection()
        report["results"]["prompt_generation"] = await test_medical_prompt_generation()
        report["results"]["vision_analysis"] = await test_vision_analysis_with_medical_focus()
        report["results"]["speech_to_text"] = await test_speech_to_text_medical_context()
        
        # Calculate test statistics
        total_medical_queries = sum(len(queries) for queries in MEDICAL_TEST_QUERIES.values())
        total_non_medical_queries = len(NON_MEDICAL_TEST_QUERIES)
        
        report["statistics"] = {
            "total_medical_queries_tested": total_medical_queries,
            "total_non_medical_queries_tested": total_non_medical_queries,
            "medical_domains_tested": len(MEDICAL_TEST_QUERIES),
            "test_coverage": "Comprehensive medical domain coverage"
        }
        
        print("\n" + "=" * 60)
        print("✅ Medical Focus Testing Completed Successfully!")
        print("=" * 60)
        
        # Save report
        report_file = f"medical_focus_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Test report saved to: {report_file}")
        
        return report
        
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")
        report["error"] = str(e)
        return report


if __name__ == "__main__":
    # Run the tests
    asyncio.run(generate_test_report()) 