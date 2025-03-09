# Face Detection Application

A lightweight Python application that performs real-time face detection using your webcam, logs detections, and provides audio greetings when faces are detected.

## Features

- Real-time face detection using OpenCV
- Audio greeting when a face is detected
- Logging of all face detections to file
- Cooldown system to prevent repeated greetings
- Simple visualization with bounding boxes

## Requirements

- Xubuntu running on Mac hardware
- Python 3.6+
- Webcam or camera
- Audio output capability

## Installation

### Automatic Installation (Recommended)

The easiest way to install is using the provided installation script which automates the entire process:

```bash
# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

The script will:
- Check if you're running on a Linux system
- Install all necessary system dependencies
- Create a Python virtual environment
- Install Python package dependencies
- Set up required directories
- Configure user permissions for camera and audio
- Provide instructions for running the application

### Manual Installation

If you prefer to install manually, follow these steps:

#### 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-dev python3-pip python3-venv
sudo apt install -y espeak
```

#### 2. Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Ensure camera and audio permissions

```bash
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER
```

You may need to log out and log back in for these changes to take effect.

#### 5. Create necessary directories

```bash
mkdir -p logs data/audio
```

## Usage

1. Activate the virtual environment:

```bash
source venv/bin/activate
```

2. Run the application:

```bash
python main.py
```

3. The application will open a window showing the camera feed with face detection.

4. When a face is detected:
   - A green rectangle will be drawn around the face
   - An audio greeting will be played
   - The detection will be logged to the `logs` directory

5. To exit the application, press 'q' while the window is in focus.

## Project Structure

```
face-rec/
├── main.py              # Main face detection application
├── install.sh           # Installation script for Xubuntu
├── requirements.txt     # Python dependencies
├── venv/                # Virtual environment (created during installation)
├── logs/                # Log files of face detections
└── data/
    └── audio/           # Audio files for greetings
```

## Technical Details

This application uses:
- OpenCV's Haar cascade classifiers for face detection
- The espeak software for text-to-speech conversion (to create the greeting sound)
- playsound for audio playback

These technologies were chosen for their simplicity and reliability on Linux systems.

## Troubleshooting

### Camera not working

If the camera fails to open:
- Ensure your camera is properly connected
- Check if another application is using the camera
- Verify you have the necessary permissions

### Audio not working

If audio greetings are not playing:
- Check your system volume settings
- Ensure audio output device is properly connected
- Make sure espeak is installed: `sudo apt install espeak`

### Face detection performance issues

If face detection is slow or laggy:
- Reduce camera resolution in the code
- Ensure adequate lighting for better face detection
- Close other resource-intensive applications

### Installation issues

If you encounter problems during installation:
- Make sure you have a stable internet connection
- Try installing system dependencies manually
- Check for error messages in the terminal
- Ensure you have sufficient disk space

## License

MIT 