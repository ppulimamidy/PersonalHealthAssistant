#!/usr/bin/env python3
"""
Fix model imports in health analytics service
"""

import re

def fix_imports():
    """Fix all incorrect model imports"""
    
    # Read the analytics service file
    with open('services/health_analytics.py', 'r') as f:
        content = f.read()
    
    # Fix HealthDevice -> Device
    content = re.sub(r'from \.\.models\.devices import HealthDevice', 
                    'from ..models.devices import Device', content)
    content = re.sub(r'HealthDevice\(', 'Device(', content)
    content = re.sub(r'HealthDevice\.', 'Device.', content)
    
    # Fix HealthAlert -> Alert
    content = re.sub(r'from \.\.models\.alerts import HealthAlert', 
                    'from ..models.alerts import Alert', content)
    content = re.sub(r'HealthAlert\(', 'Alert(', content)
    content = re.sub(r'HealthAlert\.', 'Alert.', content)
    
    # Write the fixed content back
    with open('services/health_analytics.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed model imports in health_analytics.py")

if __name__ == "__main__":
    fix_imports() 