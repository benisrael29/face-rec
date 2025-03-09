#!/usr/bin/env python3
"""
Setup Script for Face Recognition Application
--------------------------------------------
This script creates the necessary directory structure and verifies
system requirements for the face recognition application.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_system():
    """Check system compatibility"""
    print_header("System Check")
    
    # Check Python version
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    if int(python_version.split('.')[0]) < 3 or int(python_version.split('.')[1]) < 6:
        print("⚠️  Warning: This application requires Python 3.6 or higher.")
    else:
        print("✓ Python version is compatible.")
    
    # Check operating system
    os_name = platform.system()
    print(f"Operating system: {os_name}")
    if os_name != "Linux":
        print("⚠️  Warning: This application is designed to run on Linux (Xubuntu).")
    
    # Check for camera
    try:
        import cv2
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            ret, frame = camera.read()
            if ret:
                print("✓ Camera is working.")
            else:
                print("⚠️  Warning: Camera opened but could not capture frame.")
            camera.release()
        else:
            print("⚠️  Warning: Could not open camera. The application requires a webcam.")
    except ImportError:
        print("⚠️  Warning: OpenCV not installed. Run 'pip install -r requirements.txt'")
    except Exception as e:
        print(f"⚠️  Warning: Camera check failed: {str(e)}")
    
    # Check for audio capability
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if voices:
            print("✓ Text-to-speech engine is working.")
        else:
            print("⚠️  Warning: Text-to-speech engine initialized but no voices found.")
    except ImportError:
        print("⚠️  Warning: pyttsx3 not installed. Run 'pip install -r requirements.txt'")
    except Exception as e:
        print(f"⚠️  Warning: Audio check failed: {str(e)}")

def create_directories():
    """Create necessary directories for the application"""
    print_header("Creating Directories")
    
    directories = [
        "logs",
        "data",
        "data/trained_faces",
        "data/face_images"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

def check_dependencies():
    """Check if all required Python packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        "opencv-python",
        "face_recognition",
        "numpy",
        "pillow",
        "pyttsx3",
        "python-dateutil"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} is installed.")
        except ImportError:
            print(f"✗ {package} is not installed. Run 'pip install -r requirements.txt'")

def main():
    """Main setup function"""
    print_header("Face Recognition Application Setup")
    print("This script will set up the necessary environment for the face recognition application.")
    
    # Create directories
    create_directories()
    
    # Check system compatibility
    check_system()
    
    # Check dependencies
    check_dependencies()
    
    print_header("Setup Complete")
    print("""
Next steps:
1. Install any missing dependencies with: pip install -r requirements.txt
2. Train the system to recognize faces: python face_trainer.py
3. Run the main application: python main.py
    """)

if __name__ == "__main__":
    main() 