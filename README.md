# Face Detection Application

A lightweight Python application that performs real-time face detection using your webcam, logs detections, and provides audio greetings when faces are detected. Fully compatible with Python 3.12.

## Features

- Real-time face detection using OpenCV
- Persistent face tracking that maintains face identity even with movement
- Audio greeting when a face is detected
- Sequential greetings that play different messages on each encounter with the same face
- Automatic photo capture of each detected face with universal read permissions
- Customizable voice greeting using your own recorded voice
- Individual face greeting counter that tracks each detected face separately
- Daily total greeting counter with persistent storage
- Logging of all face detections to file
- One-minute cooldown system to prevent too frequent greetings
- Simple visualization with bounding boxes

## Requirements

- Xubuntu running on Mac hardware
- Python 3.6+ (including Python 3.12)
- Webcam or camera
- Audio output capability
- Microphone (for custom voice recording)

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
sudo apt install -y libsdl2-dev libsdl2-mixer-2.0-0
sudo apt install -y libsndfile1-dev  # Required for audio recording
```

#### 2. Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python dependencies

```bash
pip install --upgrade pip setuptools wheel
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
mkdir -p logs data/audio data/custom data/stats data/photos
```

## Usage

1. Activate the virtual environment:

```bash
source venv/bin/activate
```

2. Run the setup script (which includes recording your custom greeting):

```bash
python setup.py
```

3. Or run the application directly:

```bash
python main.py
```

4. The application will open a window showing the camera feed with face detection.

5. When a face is detected:
   - A green rectangle will be drawn around the face
   - An audio greeting will be played (either your custom voice or a random language)
   - The individual face greeting counter is incremented and displayed below the face
   - The total daily greeting count is incremented
   - The detection will be logged to the `logs` directory
   - A photo of the face will be saved to the `data/photos` directory

6. To exit the application, press 'q' while the window is in focus.

### Improved Face Recognition

The application uses a robust face tracking algorithm that can maintain face identity even when people move:

- Each detected face gets a persistent ID that remains consistent across frames
- The system can track the same face even when it moves, turns, or temporarily leaves the frame
- Face identity is maintained based on position, size, and movement patterns
- This allows for accurate per-face greeting counts even with natural movement

### Face Greeting Counter

The application keeps track of how many times each individual face has been greeted:

- Each detected face gets its own greeting counter, shown underneath the face
- The total daily greeting count is displayed in the top-right corner of the window
- Individual counters only increment when a greeting is actually played (not during cooldown periods)
- A one-minute cooldown prevents the same face from being greeted too frequently
- All counters automatically reset at midnight
- Data persists between application restarts (stored in data/stats directory)
- Individual face counts and total count are stored in JSON format for each day (e.g., `stats_20230415.json`)

### Face Photo Capture

The application automatically saves a photo of each detected face:

- When a new face is detected, a cropped photo of the face is saved
- Photos are saved in the `data/photos` directory with permissions that allow anyone to view them
- File permissions are set to 644 (rw-r--r--) so any user can open and view the images
- Directory permissions are set to 755 (rwxr-xr-x) so any user can access the photos directory
- Filenames include the face ID and timestamp (e.g., `face_1_20230415_120530.jpg`)
- Photos can be used for reviewing who was detected or for creating a face database

These photos can be useful for:
- Keeping a record of who was detected
- Troubleshooting face detection issues
- Creating your own face recognition dataset
- Security and monitoring purposes
- Sharing detection data with other users on the system

The photos are cropped around the face with a small margin to focus on the person while maintaining privacy by not storing the entire scene.

### Sequential Greetings

The application can now play different greeting messages each time the same face is detected:

```bash
# Record multiple greetings during setup
python setup.py

# Run the app with sequential greetings
python main.py --sequential-greetings
```

When using the setup script:
1. You can record a default greeting that plays when no specific encounter greeting exists
2. You can record numbered encounter greetings (1st, 2nd, 3rd, etc.) that play on those specific encounters
3. The app tracks how many times each face has been greeted and plays the appropriate message
4. You can exit the recording process at any time and continue to the application

Example workflow:
- First time a face is detected: plays "greeting_1.wav" ("Hello, nice to meet you!")
- Second time: plays "greeting_2.wav" ("Welcome back!")  
- Third time: plays "greeting_3.wav" ("You again? You must really like this app!")
- Fourth time and beyond: plays "default_greeting.wav" if no specific greeting exists

This feature is perfect for creating a more personalized and engaging experience with returning users.

### Custom Voice Greeting

The application now supports using your own voice as the greeting:

```bash
# Record your voice during setup
python setup.py

# Run the app with your custom greeting
python main.py --custom-greeting
```

When you run the setup script, you'll be prompted to record a short greeting (5 seconds). 
This greeting will be saved and can be used when running the application with the `--custom-greeting` flag.

### Using with Specific Camera Devices

The application supports specifying which camera to use:

```bash
# List all available cameras
python main.py --list-cameras

# Use a specific camera by index
python main.py --camera=1

# Or use a specific camera by device path
python main.py --camera=/dev/video0

# Use a specific camera with your custom greeting
python main.py --camera=1 --custom-greeting
```

## MacBook Camera Setup

If you're running Xubuntu on a MacBook and having issues with the camera, we've provided a special script to help fix those issues:

```bash
# Make the script executable
chmod +x fix_macbook_camera.sh

# Run the camera fix script
sudo ./fix_macbook_camera.sh
```

This script will:
1. Check for available camera devices
2. Install necessary drivers for MacBook cameras
3. Fix permission issues
4. Test the camera functionality
5. Guide you through next steps

### Common MacBook Camera Issues

1. **Missing drivers**: Apple's FaceTime HD cameras require special drivers on Linux
2. **Permission issues**: The user needs proper permissions to access camera devices
3. **Device path**: MacBook cameras may appear at different device paths than standard webcams

After running the fix script, try the application again with specific camera paths:

```bash
# Check which cameras are available
python main.py --list-cameras

# Try different devices
python main.py --camera=/dev/video0
python main.py --camera=/dev/video1
```

## Project Structure

```
face-rec/
├── main.py                # Main face detection application
├── setup.py               # Setup script with voice recording
├── install.sh             # Installation script for Xubuntu
├── fix_macbook_camera.sh  # MacBook camera fix script
├── requirements.txt       # Python dependencies
├── venv/                  # Virtual environment (created during installation)
├── logs/                  # Log files of face detections
└── data/
    ├── audio/             # Audio files for language greetings
    ├── custom/            # Custom voice recordings
    ├── photos/            # Saved face photos
    └── stats/             # Daily face greeting statistics
```

## Technical Details

This application uses:
- OpenCV's Haar cascade classifiers for face detection
- Custom tracking algorithm to maintain face identity across frames
- The espeak software for text-to-speech conversion (for language greetings)
- sounddevice and soundfile for recording your custom voice greeting
- Pygame for audio playback
- JSON for storing daily face greeting statistics
- All packages are compatible with Python 3.12

These technologies were chosen for their simplicity, reliability, and compatibility with modern Python versions on Linux systems.

## Dependencies

- **opencv-python (4.8.1.78)**: For camera access and face detection
- **numpy (1.26.2)**: For numerical operations
- **pygame (2.5.2)**: For audio playback
- **python-dateutil (2.8.2)**: For date handling
- **sounddevice (0.4.6)**: For audio recording
- **soundfile (0.12.1)**: For saving audio recordings

## Troubleshooting

### Camera not working

If the camera fails to open:
- Run the diagnostic tool: `python main.py --list-cameras`
- For MacBooks, run the fix script: `sudo ./fix_macbook_camera.sh`
- Try third-party camera testing apps like Cheese: `cheese`
- Ensure your camera is properly connected and enabled in firmware
- Check if another application is using the camera
- Verify you have the necessary permissions

### MacBook-specific Camera Issues

MacBooks with FaceTime HD cameras require special drivers:
1. Check if your camera is recognized: `ls -l /dev/video*`
2. Install the bcwc_pcie driver if needed (our fix script does this)
3. Verify the driver is loaded: `lsmod | grep facetimehd`
4. Make sure you're in the 'video' group: `groups | grep video`
5. After fixing drivers, always reboot your system

### Audio not working

If audio greetings are not playing:
- Check your system volume settings
- Ensure audio output device is properly connected
- Make sure espeak and SDL libraries are installed: 
  ```bash
  sudo apt install espeak libsdl2-dev libsdl2-mixer-2.0-0
  ```

### Microphone not working

If you can't record your voice during setup:
- Check if your microphone is properly connected and enabled
- Install required dependencies:
  ```bash
  sudo apt install libsndfile1-dev
  ```
- Verify your user has permission to access audio devices
- Try testing your microphone with another application
- Run a quick test with sounddevice:
  ```python
  python -c "import sounddevice as sd; print(sd.query_devices())"
  ```

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