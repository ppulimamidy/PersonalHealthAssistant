#!/usr/bin/env python3
"""
Fix Pydantic v2 configuration issues in food recognition models
"""

import re

def fix_pydantic_config():
    """Fix Pydantic v2 configuration in food recognition models"""
    
    file_path = "models/food_recognition_models.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix Config class to model_config
    content = re.sub(
        r'class Config:\s*\n\s*schema_extra\s*=\s*{',
        'model_config = {\n        "json_schema_extra": {',
        content
    )
    
    # Fix protected namespace warning for model_used field
    content = re.sub(
        r'model_used: RecognitionModel = Field\(\.\.\., description="Model used for recognition"\)',
        'model_used: RecognitionModel = Field(..., description="Model used for recognition", alias="model_used")',
        content
    )
    
    # Add protected_namespaces configuration
    content = re.sub(
        r'model_config = {',
        'model_config = {\n        "protected_namespaces": (),',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed Pydantic v2 configuration issues")

if __name__ == "__main__":
    fix_pydantic_config() 