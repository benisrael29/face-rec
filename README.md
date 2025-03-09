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

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-dev cmake build-essential libcairo2-dev libgirepository1.0-dev
sudo apt install -y portaudio19-dev python3-pyaudio
```

### 2. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Ensure camera and audio permissions

Make sure your user has permissions to access the webcam and audio devices:

```bash
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER
```

You may need to log out and log back in for these changes to take effect.

### 4. Run the setup script

The setup script will create the necessary directories and verify that your system meets the requirements:

```bash
python3 setup.py
```

## Usage

### Face Recognition Application

1. Run the main application:

```bash
python3 main.py
```

2. The application will open a window showing the camera feed with face detection.

3. When a face is detected:
   - A green rectangle will be drawn around the face
   - An audio greeting will be played
   - The detection will be logged to the `logs` directory
   - If the face is recognized, it will be greeted by name

4. To exit the application, press 'q' while the window is in focus.

### Face Training Utility

To train the system to recognize specific faces:

1. Run the face trainer:

```bash
python3 face_trainer.py
```

2. Choose option 1 to add a new face.

3. Enter the person's name when prompted.

4. Position your face in front of the camera and press the spacebar to capture samples.
   - The system will take 5 samples of your face from different angles
   - You'll need to press the spacebar for each sample

5. Once training is complete, run the main application to see the recognition in action.

## Project Structure

```
face-rec/
├── main.py              # Main face recognition application
├── face_trainer.py      # Utility to train the system on new faces
├── setup.py             # Setup script to initialize directories
├── requirements.txt     # Python dependencies
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
- Run `python3 -m pyttsx3` to test the text-to-speech engine

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

## License

MIT 