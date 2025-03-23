#!/usr/bin/env python3
"""
Setup Script for Face Detection Application
--------------------------------------------
This script creates a virtual environment, installs dependencies from
requirements.txt, and runs the face detection application.
"""

import os
import sys
import platform
import subprocess
import time
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️  {message}")

def print_error(message):
    """Print an error message"""
    print(f"✗ {message}")

def run_command(command, shell=False):
    """Run a command and return success status"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        result = subprocess.run(command, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def check_python():
    """Check Python version"""
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    
    if int(python_version.split('.')[0]) < 3 or int(python_version.split('.')[1]) < 6:
        print_warning("This application requires Python 3.6 or higher.")
        return False
    else:
        print_success("Python version is compatible.")
        return True

def setup_virtual_environment():
    """Create and activate a virtual environment"""
    print_header("Setting up Virtual Environment")
    
    venv_dir = "venv"
    
    # Check if venv already exists
    if Path(venv_dir).exists():
        print_warning(f"Virtual environment already exists at {venv_dir}")
        return True
    
    print(f"Creating virtual environment in {venv_dir}...")
    if run_command([sys.executable, "-m", "venv", venv_dir]):
        print_success("Virtual environment created successfully.")
        return True
    else:
        print_error("Failed to create virtual environment.")
        return False

def get_venv_python():
    """Get path to Python in virtual environment"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def get_venv_pip():
    """Get path to pip in virtual environment"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    else:
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print_header("Installing Dependencies")
    
    pip_path = get_venv_pip()
    
    # Upgrade pip first
    print("Upgrading pip...")
    run_command([pip_path, "install", "--upgrade", "pip"])
    
    # Install requirements
    print("Installing dependencies from requirements.txt...")
    if run_command([pip_path, "install", "-r", "requirements.txt"]):
        print_success("Successfully installed all dependencies.")
        return True
    else:
        print_error("Failed to install dependencies.")
        return False

def create_directories():
    """Create necessary directories for the application"""
    print_header("Creating Directories")
    
    directories = [
        "logs",
        "data/audio",
        "data/custom"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    return True

def record_custom_greeting():
    """Record user's voice for custom greeting"""
    print_header("Custom Voice Recording")
    
    # Check if custom greeting already exists
    custom_greeting_path = Path("data/custom/my_greeting.wav")
    
    if custom_greeting_path.exists():
        choice = input("Custom greeting already exists. Record a new one? (y/n): ").strip().lower()
        if choice != 'y':
            print_success("Using existing custom greeting.")
            return True
    
    print("You will be prompted to record your voice as a custom greeting.")
    print("Please speak clearly after the countdown.")
    print("Recording will automatically stop after 5 seconds.")
    
    # Check if sounddevice and soundfile are installed in virtual environment
    python_path = get_venv_python()
    
    try:
        # Create a temporary Python script for recording
        temp_script_path = "temp_record.py"
        with open(temp_script_path, "w") as f:
            f.write("""
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import time

def record_audio(output_file, seconds=5, samplerate=44100):
    print("\\nRecording will begin in:")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("Recording... Speak now!")
    
    # Record audio
    recording = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    
    print("Recording finished!")
    
    # Make sure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save as WAV file
    sf.write(output_file, recording, samplerate)
    
    print(f"Audio saved to {output_file}")
    return True

# Record audio
record_audio("data/custom/my_greeting.wav")
""")
        
        # Run the recording script
        if run_command([python_path, temp_script_path]):
            print_success("Successfully recorded custom greeting.")
            # Remove temporary script
            os.remove(temp_script_path)
            return True
        else:
            print_error("Failed to record custom greeting.")
            # Remove temporary script
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            return False
            
    except Exception as e:
        print_error(f"Error during recording: {e}")
        return False

def run_application():
    """Run the face detection application"""
    print_header("Running Face Detection Application")
    
    python_path = get_venv_python()
    
    print("Starting application...")
    print("Press 'q' to quit when the application window is active.")
    print("")
    
    # Run the application
    try:
        subprocess.run([python_path, "main.py", "--custom-greeting"])
        return True
    except Exception as e:
        print_error(f"Failed to run application: {e}")
        return False

def main():
    """Main setup function"""
    print_header("Face Detection Application Setup")
    print("This script will set up the environment and run the application.")
    
    # Check Python version
    if not check_python():
        print_error("Incompatible Python version. Please use Python 3.6 or higher.")
        sys.exit(1)
    
    # Set up virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Record custom greeting
    record_custom_greeting()
    
    # Run the application
    run_application()

if __name__ == "__main__":
    main() 