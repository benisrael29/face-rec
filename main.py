#!/usr/bin/env python3
"""
Face Recognition Application
----------------------------
This application captures video from a camera, performs face recognition,
logs when faces are detected, and greets detected people via audio.
"""

import os
import cv2
import time
import pickle
import logging
import datetime
import threading
import numpy as np
import face_recognition
import pyttsx3

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

# Path to load encodings
ENCODINGS_FILE = 'data/trained_faces/encodings.pkl'

class FaceRecognitionApp:
    def __init__(self):
        # Initialize the camera
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera. Please check your camera connection.")
        
        # Set camera resolution to optimize performance
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        
        # For tracking faces we've already greeted
        self.last_greeting_time = {}
        self.greeting_cooldown = 10  # seconds between greetings for the same face
        
        # Load known face encodings if available
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()
        
        logger.info("Face Recognition App initialized")
    
    def load_known_faces(self):
        """Load known face encodings from disk if available"""
        if os.path.exists(ENCODINGS_FILE):
            logger.info(f"Loading known face encodings from {ENCODINGS_FILE}")
            try:
                with open(ENCODINGS_FILE, 'rb') as f:
                    data = pickle.load(f)
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']
                logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            except Exception as e:
                logger.error(f"Error loading face encodings: {str(e)}")
        else:
            logger.info("No known face encodings found. Run face_trainer.py to train the system.")
    
    def speak(self, text):
        """Speak the given text in a non-blocking way"""
        # Run speech in a separate thread so it doesn't block video processing
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
    
    def _speak_thread(self, text):
        """Internal method to handle speech in a separate thread"""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def process_frame(self, frame):
        """Process a single frame for face detection and recognition"""
        # Resize frame for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert from BGR (OpenCV format) to RGB (face_recognition format)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        # Return early if no faces detected
        if not face_locations:
            return frame
        
        # Get face encodings for each face in the frame
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        # Log and greet for each detected face
        current_time = time.time()
        
        for (face_location, face_encoding) in zip(face_locations, face_encodings):
            # Scale back up face locations since we detected in a scaled down image
            top, right, bottom, left = [coord * 4 for coord in face_location]
            
            # Create a simple face ID based on location (for cooldown purposes)
            face_id = f"{top}_{right}_{bottom}_{left}"
            
            # Try to recognize the face
            name = "Unknown"
            if self.known_face_encodings:
                # Compare face with known faces
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                
                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
            
            # Draw a box around the face and label with name
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            
            # Log the detection
            if name == "Unknown":
                logger.info(f"Unknown face detected at coordinates: top={top}, right={right}, bottom={bottom}, left={left}")
            else:
                logger.info(f"Recognized {name} at coordinates: top={top}, right={right}, bottom={bottom}, left={left}")
            
            # Check if we should greet this face (based on cooldown)
            if face_id not in self.last_greeting_time or \
               (current_time - self.last_greeting_time[face_id]) > self.greeting_cooldown:
                
                if name == "Unknown":
                    self.speak("Hello there!")
                else:
                    self.speak(f"Hello {name}!")
                
                self.last_greeting_time[face_id] = current_time
                logger.info(f"Greeting sent for {'recognized face: ' + name if name != 'Unknown' else 'unknown face'}")
        
        return frame
    
    def run(self):
        """Main application loop"""
        logger.info("Starting face recognition loop")
        
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
                cv2.imshow('Face Recognition', processed_frame)
                
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
            logger.info("Application terminated")

if __name__ == "__main__":
    try:
        app = FaceRecognitionApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
