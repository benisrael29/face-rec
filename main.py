#!/usr/bin/env python3
"""
Face Detection Application
----------------------------
This application captures video from a camera, performs face detection,
logs when faces are detected, and greets detected people via audio.
"""

import os
import cv2
import time
import logging
import datetime
import subprocess
import argparse
import numpy as np
import pygame
from pathlib import Path

# Parse command line arguments
parser = argparse.ArgumentParser(description='Face Detection Application')
parser.add_argument('--camera', type=str, default=None, 
                    help='Camera device path (e.g., /dev/video0) or index (e.g., 0, 1)')
args = parser.parse_args()

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/face_detection_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure the sounds directory exists and create the audio folder if it doesn't
os.makedirs('data/audio', exist_ok=True)

# Initialize pygame mixer for audio
pygame.mixer.init()

class FaceDetectionApp:
    def __init__(self, camera_source=None):
        # Initialize the camera
        self.camera = None
        self.init_camera(camera_source)
        
        # Set camera resolution to optimize performance
        if self.camera and self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Load the face cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier. Check OpenCV installation.")
        
        # For tracking faces we've already greeted
        self.last_greeting_time = {}
        self.greeting_cooldown = 10  # seconds between greetings for the same face
        
        # Create greeting sound file if it doesn't exist
        self.greeting_sound = "data/audio/hello.wav"
        if not os.path.exists(self.greeting_sound):
            self._create_greeting_sound()
        
        # Load the greeting sound
        try:
            pygame.mixer.music.load(self.greeting_sound)
        except Exception as e:
            logger.error(f"Failed to load greeting sound: {str(e)}")
        
        logger.info("Face Detection App initialized")
    
    def init_camera(self, camera_source=None):
        """Initialize camera with various fallback options"""
        if self.camera is not None and self.camera.isOpened():
            self.camera.release()
            
        # Try the specified camera source first if provided
        if camera_source is not None:
            try:
                # Check if the camera_source is a string path to a device
                if isinstance(camera_source, str) and camera_source.startswith('/dev/'):
                    self.camera = cv2.VideoCapture(camera_source)
                    if self.camera.isOpened():
                        logger.info(f"Camera opened successfully using device: {camera_source}")
                        return
                
                # Try as an integer index or string that can be converted to int
                try:
                    camera_idx = int(camera_source)
                    self.camera = cv2.VideoCapture(camera_idx)
                    if self.camera.isOpened():
                        logger.info(f"Camera opened successfully using index: {camera_idx}")
                        return
                except ValueError:
                    # If it's not an integer or path, log and continue to fallbacks
                    logger.warning(f"Could not interpret camera source: {camera_source}")
            except Exception as e:
                logger.error(f"Error opening specified camera source {camera_source}: {str(e)}")
        
        # Try different indices if no specific source was given or it failed
        for idx in range(10):  # Try indices 0-9
            try:
                logger.info(f"Trying to open camera with index {idx}...")
                self.camera = cv2.VideoCapture(idx)
                if self.camera.isOpened():
                    # Read a test frame to ensure it's working
                    ret, _ = self.camera.read()
                    if ret:
                        logger.info(f"Successfully opened camera with index {idx}")
                        return
                    else:
                        logger.warning(f"Camera with index {idx} opened but failed to read frame")
                        self.camera.release()
                else:
                    logger.warning(f"Failed to open camera with index {idx}")
            except Exception as e:
                logger.error(f"Error trying camera index {idx}: {str(e)}")
        
        # Try common device paths for MacBooks
        mac_camera_paths = [
            '/dev/video0', 
            '/dev/video1', 
            '/dev/video2',
            '/dev/avfoundation',  # This might work with gstreamer backend
            '/dev/facetime', 
            '/dev/facetimehd'
        ]
        
        for path in mac_camera_paths:
            try:
                logger.info(f"Trying to open camera with device path: {path}")
                self.camera = cv2.VideoCapture(path)
                if self.camera.isOpened():
                    ret, _ = self.camera.read()
                    if ret:
                        logger.info(f"Successfully opened camera with device path: {path}")
                        return
                    else:
                        logger.warning(f"Camera with path {path} opened but failed to read frame")
                        self.camera.release()
                else:
                    logger.warning(f"Failed to open camera with path: {path}")
            except Exception as e:
                logger.error(f"Error trying camera path {path}: {str(e)}")
        
        # If all attempts fail
        logger.error("Failed to open any camera. Please check your camera connection.")
        self.camera = cv2.VideoCapture(0)  # Set to default for object consistency
        raise RuntimeError("Could not open camera. Please check your camera connection.")
    
    def _create_greeting_sound(self):
        """Create a greeting sound file using espeak (if available)"""
        try:
            # Use espeak to create an audio file (WAV format for better compatibility)
            subprocess.run(
                ["espeak", "-w", self.greeting_sound, "Hello there!"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"Created greeting sound file: {self.greeting_sound}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Failed to create greeting sound: {str(e)}")
            # Create an empty file so we don't keep trying to create it
            Path(self.greeting_sound).touch()
    
    def speak(self):
        """Play the greeting sound"""
        try:
            # Check if music is currently playing
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play()
                logger.info("Played greeting sound")
        except Exception as e:
            logger.error(f"Failed to play sound: {str(e)}")
    
    def process_frame(self, frame):
        """Process a single frame for face detection"""
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Return early if no faces detected
        if len(faces) == 0:
            return frame
        
        # Log and greet for each detected face
        current_time = time.time()
        
        for (x, y, w, h) in faces:
            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Create a simple face ID based on location (for cooldown purposes)
            face_id = f"{x}_{y}_{w}_{h}"
            
            # Log the detection
            logger.info(f"Face detected at coordinates: x={x}, y={y}, width={w}, height={h}")
            
            # Check if we should greet this face (based on cooldown)
            if face_id not in self.last_greeting_time or \
               (current_time - self.last_greeting_time[face_id]) > self.greeting_cooldown:
                
                self.speak()
                self.last_greeting_time[face_id] = current_time
                logger.info("Greeting sent for detected face")
        
        return frame
    
    def run(self):
        """Main application loop"""
        logger.info("Starting face detection loop")
        
        try:
            while True:
                # Check if camera is opened
                if not self.camera.isOpened():
                    logger.error("Camera connection lost. Attempting to reconnect...")
                    try:
                        self.init_camera()
                    except RuntimeError:
                        logger.error("Failed to reconnect to camera. Exiting...")
                        break
                
                # Capture frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("Failed to capture frame from camera")
                    # Try to reinitialize the camera
                    try:
                        logger.info("Attempting to reinitialize camera...")
                        self.init_camera()
                        continue
                    except RuntimeError:
                        break
                
                # Process the frame (detect faces, log, and potentially speak)
                processed_frame = self.process_frame(frame)
                
                # Display the resulting frame
                cv2.imshow('Face Detection', processed_frame)
                
                # Break loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        finally:
            # Release resources
            if self.camera is not None:
                self.camera.release()
            cv2.destroyAllWindows()
            pygame.mixer.quit()
            logger.info("Application terminated")

def list_available_cameras():
    """List available camera devices and indices"""
    print("Searching for available cameras...")
    
    # Try different indices
    found_cameras = []
    for idx in range(10):  # Try indices 0-9
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                found_cameras.append(f"Index {idx}: Available")
            else:
                found_cameras.append(f"Index {idx}: Opens but can't read frames")
            cap.release()
        else:
            found_cameras.append(f"Index {idx}: Not available")
    
    # Try to list video devices in /dev if on Linux
    try:
        import subprocess
        result = subprocess.run(["ls", "-l", "/dev/video*"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        if result.returncode == 0:
            print("\nDetected video devices:")
            print(result.stdout)
        else:
            print("\nNo video devices found in /dev or can't access them.")
    except:
        print("Could not check for video devices in /dev (might not be on Linux or insufficient permissions)")
    
    print("\nCamera availability:")
    for cam in found_cameras:
        print(cam)
    
    print("\nTo use a specific camera, run the app with:")
    print("python main.py --camera=INDEX_OR_PATH")
    print("Example: python main.py --camera=1")
    print("Example: python main.py --camera=/dev/video0")

if __name__ == "__main__":
    try:
        if len(os.sys.argv) > 1 and os.sys.argv[1] == "--list-cameras":
            list_available_cameras()
        else:
            app = FaceDetectionApp(args.camera)
            app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Error: {str(e)}")
        print("To list available cameras, run: python main.py --list-cameras")
