#!/usr/bin/env python3

import sys
import os
import subprocess

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Change to the project directory
os.chdir(project_root)

print("Starting OpenSLAM Backend Server...")
print("Project root:", project_root)
print("Python path:", sys.path[0])

try:
    print("Backend server starting on http://localhost:8007")
    print("API documentation available at http://localhost:8007/docs")
    
    # Run uvicorn directly with the app module
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8007, reload=False)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)