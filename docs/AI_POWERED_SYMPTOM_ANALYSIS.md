# AI-Powered Symptom Analysis

## Overview

The Personal Health Assistant now features advanced AI-powered symptom analysis that generates personalized, context-aware responses for any medical or health issue. Unlike static rule-based systems, this implementation uses OpenAI's GPT-4 model to dynamically generate:

- **Follow-up questions** specific to the symptoms
- **Personalized recommendations** based on medical context
- **Multi-model insights** with evidence-based analysis
- **Urgency assessments** tailored to the specific condition

## Key Features

### 1. Dynamic Follow-up Question Generation

The system now generates relevant follow-up questions on-the-fly using AI, rather than relying on predefined templates.

**Before (Static):**
```json
{
  "follow_up_questions": [
    {
      "id": "duration",
      "question": "How long have you been experiencing these symptoms?",
      "type": "duration",
      "required": true,
      "options": ["Less than 24 hours", "1-3 days", "1 week", "2-4 weeks", "More than 1 month"]
    }
  ]
}
```

**After (AI-Powered):**
```json
{
  "follow_up_questions": [
    {
      "id": "sun_exposure_duration",
      "question": "How long were you exposed to the sun?",
      "type": "exposure",
      "required": false,
      "options": ["Less than 30 minutes", "30 minutes - 1 hour", "1-2 hours", "2-4 hours", "More than 4 hours"]
    },
    {
      "id": "sun_protection_used",
      "question": "Did you use any sun protection?",
      "type": "protection",
      "required": false,
      "options": ["Sunscreen", "Hat/Clothing", "Both", "None", "Not sure"]
    }
  ]
}
```

### 2. Personalized Recommendation Creation

AI generates evidence-based recommendations specific to the symptoms and user context.

**Example for Sun Rash:**
```json
{
  "recommendations": [
    {
      "title": "Sun Protection",
      "description": "Apply broad-spectrum sunscreen (SPF 30+) and wear protective clothing when outdoors.",
      "category": "prevention",
      "priority": "high",
      "actionable": true,
      "evidence": ["Prevents further sun damage and reduces risk of skin cancer"],
      "follow_up": "Apply sunscreen 30 minutes before sun exposure"
    },
    {
      "title": "Cool Compress",
      "description": "Apply cool, damp cloths to the affected area to reduce inflammation and discomfort.",
      "category": "symptom_relief",
      "priority": "medium",
      "actionable": true,
      "evidence": ["Cooling reduces inflammation and provides pain relief"],
      "follow_up": "Apply for 15-20 minutes several times daily"
    }
  ]
}
```

### 3. Multi-Model Insight Generation

The system provides comprehensive medical insights using AI analysis.

**Example Insights:**
```json
{
  "insights": [
    {
      "type": "medical_knowledge",
      "title": "Sun Rash and Sunburn",
      "description": "Sun rash (polymorphous light eruption) is a common skin reaction to UV exposure, different from typical sunburn.",
      "confidence": "high",
      "source": "dermatology_guidelines"
    }
  ],
  "possible_causes": [
    {
      "cause": "Polymorphous light eruption (PMLE)",
      "confidence": "high",
      "evidence": "Common reaction to first sun exposure of the season",
      "medical_background": "Immune system reaction to UV radiation"
    }
  ]
}
```

### 4. Context-Aware Urgency Assessment

AI evaluates urgency levels based on symptom characteristics and medical knowledge.

**Example Urgency Assessment:**
```json
{
  "urgency_level": "low",
  "urgency_reasoning": "Mild to moderate sunburn can typically be managed at home with proper care.",
  "next_steps": [
    "Apply cool compresses and moisturizer",
    "Stay hydrated",
    "Avoid further sun exposure"
  ]
}
```

## Technical Implementation

### API Endpoint

**Endpoint:** `POST /health/analyze-symptoms`

**Request Body:**
```json
{
  "symptoms": ["have a sunrash on my neck"],
  "severity": "medium",
  "duration": "unknown",
  "context": "",
  "include_vitals": true,
  "include_medications": true,
  "generate_insights": true
}
```

**Response Structure:**
```json
{
  "user_id": "test-user",
  "analyzed_at": "2025-08-09T01:06:16.896833",
  "symptoms_analyzed": ["have a sunrash on my neck"],
  "severity": "medium",
  "duration": "unknown",
  "query_analysis": {
    "query_type": "general_inquiry",
    "medical_entities": [],
    "intent": "information_seeking",
    "specific_concerns": [],
    "requires_follow_up": true
  },
  "analysis": "AI-generated analysis...",
  "key_insights": [...],
  "recommendations": [...],
  "possible_causes": [...],
  "urgency_level": "low",
  "urgency_reasoning": "...",
  "follow_up_questions": [...],
  "next_steps": [...],
  "medical_context": {...},
  "data_sources": [...],
  "confidence": "medium",
  "interaction_required": true,
  "session_id": "session_test-user_1754701576"
}
```

### AI Integration

The system uses OpenAI's GPT-4 model with structured prompts to ensure consistent, medical-grade responses:

1. **Follow-up Questions:** Generated using prompts that focus on clinical relevance
2. **Recommendations:** Created with evidence-based medical knowledge
3. **Insights:** Derived from comprehensive symptom analysis
4. **Urgency Assessment:** Evaluated using medical triage principles

### Fallback Mechanisms

The system includes robust fallback mechanisms:

- **AI Failure:** Falls back to basic, predefined questions and recommendations
- **API Errors:** Graceful degradation with error logging
- **Invalid Responses:** JSON validation and error handling

## Benefits

### 1. Comprehensive Coverage
- Handles any medical symptom or health concern
- No need to maintain extensive symptom databases
- Adapts to new medical knowledge automatically

### 2. Personalization
- Context-aware responses based on user data
- Considers medical history, medications, and vitals
- Tailored urgency assessments

### 3. Medical Accuracy
- Evidence-based recommendations
- Clinical guideline compliance
- Professional medical knowledge integration

### 4. Scalability
- No manual rule maintenance required
- Handles edge cases automatically
- Supports multiple languages and medical contexts

## Testing

Use the provided test script to verify functionality:

```bash
python test_ai_symptom_analysis.py
```

This script tests various symptom types and validates:
- Dynamic question generation
- Personalized recommendations
- Multi-model insights
- Urgency assessments

## Configuration

### Environment Variables

Ensure the following environment variables are set:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Service Configuration

The AI reasoning orchestrator service should be running and accessible at:
```
http://ai-reasoning.localhost/health/analyze-symptoms
```

## Future Enhancements

1. **Multi-Modal Analysis:** Integration with image analysis for skin conditions
2. **Voice Input:** Speech-to-text for symptom description
3. **Continuous Learning:** Feedback loop for improving AI responses
4. **Specialist Integration:** Domain-specific AI models for different medical specialties
5. **Real-time Updates:** Live medical knowledge integration

## Security and Privacy

- All AI interactions are logged for audit purposes
- No personal health data is stored in AI model training
- HIPAA-compliant data handling
- Secure API key management

## Support

For technical support or questions about the AI-powered symptom analysis:

1. Check the service logs for detailed error information
2. Verify OpenAI API key configuration
3. Test with the provided test script
4. Review the API documentation for endpoint details
