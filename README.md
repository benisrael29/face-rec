# Face Recognition Application

A Python application that performs real-time face recognition using your webcam, logs detections, and provides audio greetings when faces are detected.

## Features

- Real-time face detection and recognition
- Audio greeting when a face is detected
- Personalized greetings for recognized faces
- Face training system to recognize specific people
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
sudo apt install -y python3-dev python3-pip python3-venv cmake build-essential
sudo apt install -y libx11-dev libatlas-base-dev libgtk-3-dev libboost-python-dev
sudo apt install -y espeak portaudio19-dev python3-pyaudio
# For newer Python versions (3.12+)
sudo apt install -y python3-setuptools python3-distutils
```

#### 2. Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install setuptools wheel
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
mkdir -p logs data/trained_faces data/face_images
```

## Usage

### Face Recognition Application

1. Activate the virtual environment (if you're using one):

```bash
source venv/bin/activate
```

2. Run the main application:

```bash
python main.py
```

3. The application will open a window showing the camera feed with face detection.

4. When a face is detected:
   - A green rectangle will be drawn around the face
   - An audio greeting will be played
   - The detection will be logged to the `logs` directory
   - If the face is recognized, it will be greeted by name

5. To exit the application, press 'q' while the window is in focus.

### Face Training Utility

To train the system to recognize specific faces:

1. Activate the virtual environment (if you're using one):

```bash
source venv/bin/activate
```

2. Run the face trainer:

```bash
python face_trainer.py
```

3. Choose option 1 to add a new face.

4. Enter the person's name when prompted.

5. Position your face in front of the camera and press the spacebar to capture samples.
   - The system will take 5 samples of your face from different angles
   - You'll need to press the spacebar for each sample

6. Once training is complete, run the main application to see the recognition in action.

## Project Structure

```
face-rec/
├── main.py              # Main face recognition application
├── face_trainer.py      # Utility to train the system on new faces
├── setup.py             # Setup script to initialize directories
├── install.sh           # Installation script for Xubuntu
├── requirements.txt     # Python dependencies
├── venv/                # Virtual environment (created during installation)
├── logs/                # Log files of face detections
└── data/
    ├── trained_faces/   # Saved face encodings
    └── face_images/     # Captured face images during training
```

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
- Run `python -m pyttsx3` to test the text-to-speech engine

### Face detection performance issues

If face detection is slow or laggy:
- Reduce camera resolution in the code
- Ensure adequate lighting for better face detection
- Close other resource-intensive applications

### Face recognition issues

If faces are not being recognized correctly:
- Try retraining with better lighting conditions
- Capture faces from different angles
- Adjust the recognition tolerance in the code (default is 0.6)

### Installation issues

If you encounter problems during installation:
- Make sure you have a stable internet connection
- Try installing system dependencies manually
- Check for error messages in the terminal
- Ensure you have sufficient disk space

#### "No module named 'distutils'" error

If you see an error about distutils when installing packages:

1. Install the distutils package at the system level:
   ```bash
   sudo apt install python3-setuptools python3-distutils
   ```

2. Then install setuptools inside your virtual environment:
   ```bash
   pip install setuptools
   ```

3. Continue with the regular installation process

This issue usually happens with newer Python versions (3.12+) where distutils is no longer included in the standard library.

## License

MIT 