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
import numpy as np
import pygame
from pathlib import Path

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
    def __init__(self):
        # Initialize the camera
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera. Please check your camera connection.")
        
        # Set camera resolution to optimize performance
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
                # Capture frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("Failed to capture frame from camera")
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
            self.camera.release()
            cv2.destroyAllWindows()
            pygame.mixer.quit()
            logger.info("Application terminated")

if __name__ == "__main__":
    try:
        app = FaceDetectionApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
