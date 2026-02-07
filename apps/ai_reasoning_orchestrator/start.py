#!/usr/bin/env python3
"""
Startup script for AI Reasoning Orchestrator Service
Sets up the correct Python path and starts the service
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ['PYTHONPATH'] = str(project_root)
os.environ['PYTHONUNBUFFERED'] = '1'

if __name__ == "__main__":
    import uvicorn
    from apps.ai_reasoning_orchestrator.main import app
    
    print(f"🚀 Starting AI Reasoning Orchestrator Service...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {os.environ.get('PYTHONPATH')}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8300,
        log_level="info",
        reload=True
    )
