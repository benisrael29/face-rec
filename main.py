#!/usr/bin/env python3
"""
Face Detection Application
----------------------------
This application captures video from a camera, performs face detection,
takes photos of detected faces, and greets people via audio after a buffer period.
"""

import os
import cv2
import time
import logging
import datetime
import subprocess
import argparse
import pygame
import random
import json
from pathlib import Path

# Parse command line arguments
parser = argparse.ArgumentParser(description='Face Detection Application')
parser.add_argument('--camera', type=str, default=None, 
                    help='Camera device path (e.g., /dev/video0) or index (e.g., 0, 1)')
parser.add_argument('--list-cameras', action='store_true',
                    help='List available camera devices and indices')
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

# Ensure the sounds directory exists and create required folders if they don't exist
os.makedirs('data/audio', exist_ok=True)
os.makedirs('data/photos', exist_ok=True)
os.makedirs('data/custom', exist_ok=True)

# Create photos directory with appropriate permissions
photos_dir = 'data/photos'
os.makedirs(photos_dir, exist_ok=True)
os.chmod(photos_dir, 0o755)

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
        
        # Timing variables
        self.last_greeting_time = 0
        self.greeting_cooldown = 60  # seconds between greetings
        self.face_buffer_time = 1.0  # seconds face must be visible before processing
        self.face_detection_start_time = None
        
        # Custom greeting file
        self.custom_greeting_file = "data/custom/my_greeting.wav"
        
        # Load the custom greeting sound
        try:
            if os.path.exists(self.custom_greeting_file):
                pygame.mixer.music.load(self.custom_greeting_file)
                logger.info(f"Using custom greeting from: {self.custom_greeting_file}")
            else:
                logger.warning("Custom greeting file not found. Please run setup.py first to record your greeting.")
        except Exception as e:
            logger.error(f"Failed to load greeting sound: {str(e)}")
        
        logger.info("Face Detection App initialized")
    
    def speak(self):
        """Play the custom greeting sound"""
        try:
            # Check if music is currently playing
            if not pygame.mixer.music.get_busy():
                if os.path.exists(self.custom_greeting_file):
                    # Load and play the custom greeting
                    pygame.mixer.music.load(self.custom_greeting_file)
                    pygame.mixer.music.play()
                    logger.info("Played custom greeting")
                    
                    # Update the last greeting time
                    self.last_greeting_time = time.time()
                    return True
                else:
                    logger.warning("Custom greeting file not found")
                    return False
        except Exception as e:
            logger.error(f"Failed to play sound: {str(e)}")
            return False
        
        return False
    
    def save_face_photo(self, frame, face):
        """Save a photo of the detected face"""
        try:
            # Create a timestamp for the filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create the filename
            filename = f"data/photos/face_{timestamp}.jpg"
            
            # Extract the face region with some margin
            margin = 20  # pixels of margin around the face
            y1 = max(0, face[1] - margin)
            y2 = min(frame.shape[0], face[1] + face[3] + margin)
            x1 = max(0, face[0] - margin)
            x2 = min(frame.shape[1], face[0] + face[2] + margin)
            
            face_img = frame[y1:y2, x1:x2]
            
            # Save the face image
            cv2.imwrite(filename, face_img)
            
            # Set file permissions to be readable by anyone (0o644 = rw-r--r--)
            os.chmod(filename, 0o644)
            
            logger.info(f"Saved face photo to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save face photo: {str(e)}")
            return False
    
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
            self.face_detection_start_time = None
            return frame
        
        # If this is the first frame with a face, start the buffer timer
        if self.face_detection_start_time is None:
            self.face_detection_start_time = time.time()
        
        # Calculate how long the face has been visible
        face_visible_time = time.time() - self.face_detection_start_time
        
        # Check if we've waited long enough
        if face_visible_time >= self.face_buffer_time:
            # Check if we're past the cooldown period
            if (time.time() - self.last_greeting_time) >= self.greeting_cooldown:
                # Process the first detected face
                face = faces[0]
                
                # Save photo and play greeting
                if self.save_face_photo(frame, face):
                    self.speak()
                
                # Reset the detection start time
                self.face_detection_start_time = None
        
        # Draw rectangles around all detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Display buffer time if face is detected
        if self.face_detection_start_time is not None:
            remaining_buffer = max(0, self.face_buffer_time - face_visible_time)
            cv2.putText(frame, f"Buffer: {remaining_buffer:.1f}s", (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display cooldown time if active
        if (time.time() - self.last_greeting_time) < self.greeting_cooldown:
            remaining_cooldown = round(self.greeting_cooldown - (time.time() - self.last_greeting_time))
            cv2.putText(frame, f"Cooldown: {remaining_cooldown}s", (10, 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
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
        
        # If all attempts fail
        logger.error("Failed to open any camera. Please check your camera connection.")
        self.camera = cv2.VideoCapture(0)  # Set to default for object consistency
        raise RuntimeError("Could not open camera. Please check your camera connection.")
    
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
                
                # Add instructions to the frame
                cv2.putText(processed_frame, "Press 'q' to quit", (10, frame.shape[0] - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
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
        if args.list_cameras:
            list_available_cameras()
        else:
            app = FaceDetectionApp(args.camera)
            app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Error: {str(e)}")
        print("To list available cameras, run: python main.py --list-cameras")
