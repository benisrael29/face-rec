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
import random
import json
import math
import glob
from pathlib import Path
from collections import defaultdict

# Parse command line arguments
parser = argparse.ArgumentParser(description='Face Detection Application')
parser.add_argument('--camera', type=str, default=None, 
                    help='Camera device path (e.g., /dev/video0) or index (e.g., 0, 1)')
parser.add_argument('--custom-greeting', action='store_true',
                    help='Use custom recorded greeting instead of random languages')
parser.add_argument('--sequential-greetings', action='store_true',
                    help='Use different greetings for each encounter with the same face')
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
os.makedirs('data/custom', exist_ok=True)
os.makedirs('data/stats', exist_ok=True)  # Directory for tracking statistics

# Create photos directory with appropriate permissions
photos_dir = 'data/photos'
os.makedirs(photos_dir, exist_ok=True)
# Set directory permissions to 755 (rwxr-xr-x) - Owner can read/write/execute, others can read/execute
os.chmod(photos_dir, 0o755)

# Initialize pygame mixer for audio
pygame.mixer.init()

# Define greetings in different languages
GREETINGS = {
    'English': 'Hello',
    'Spanish': 'Hola',
    'French': 'Bonjour',
    'German': 'Hallo',
    'Italian': 'Ciao',
    'Portuguese': 'Olá',
    'Japanese': 'Konnichiwa',
    'Chinese': 'Ni hao',
    'Russian': 'Privet',
    'Arabic': 'Marhaba',
    'Hindi': 'Namaste',
    'Korean': 'Annyeong',
    'Greek': 'Yassou',
    'Turkish': 'Merhaba',
    'Swedish': 'Hej',
    'Polish': 'Cześć',
    'Dutch': 'Hallo',
    'Thai': 'Sawadee',
    'Vietnamese': 'Xin chào',
    'Hebrew': 'Shalom'
}

# Voice parameters for more natural sound
VOICE_PARAMS = {
    'default': '-s 130 -p 50 -a 100',  # Standard voice
    'English': '-v en -s 130 -p 50 -a 100',
    'Spanish': '-v es -s 130 -p 50 -a 100',
    'French': '-v fr -s 130 -p 50 -a 100',
    'German': '-v de -s 130 -p 50 -a 100',
    'Italian': '-v it -s 130 -p 50 -a 100'
    # Other languages use default voice
}

class TrackedFace:
    """Class to represent a tracked face across frames"""
    next_id = 1  # Class variable to assign unique IDs
    
    def __init__(self, x, y, w, h):
        self.id = f"face_{TrackedFace.next_id}"
        TrackedFace.next_id += 1
        self.update_position(x, y, w, h)
        self.frames_missing = 0
        self.last_greeting_time = 0
        self.encounter_count = 0  # Track how many times this face has been greeted
        
    def update_position(self, x, y, w, h):
        """Update the face's position"""
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.centerX = x + w // 2
        self.centerY = y + h // 2
        self.frames_missing = 0
        
    def distance_to(self, x, y, w, h):
        """Calculate distance to another face position based on centers"""
        other_centerX = x + w // 2
        other_centerY = y + h // 2
        
        # Euclidean distance between centers
        distance = math.sqrt(
            (self.centerX - other_centerX) ** 2 + 
            (self.centerY - other_centerY) ** 2
        )
        
        # Also consider size difference as a factor
        size_diff = abs((self.w * self.h) - (w * h)) / max((self.w * self.h), (w * h))
        
        # Weighted combination
        return distance + (size_diff * 100)  # Weight size difference

class FaceDetectionApp:
    def __init__(self, camera_source=None, use_custom_greeting=False, use_sequential_greetings=False):
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
        
        # Face tracking variables
        self.tracked_faces = []
        self.max_missing_frames = 10  # Frames before considering a face gone
        self.same_face_threshold = 100  # Maximum distance to consider it the same face
        self.saved_face_photos = set()  # Keep track of faces we've saved photos for
        
        # Greeting cooldown
        self.greeting_cooldown = 10  # seconds between greetings for the same face
        
        # Global cooldown to prevent rapid greetings for different faces
        self.last_global_greeting_time = 0
        self.global_greeting_cooldown = 3  # seconds between any greetings
        
        # Custom greeting option
        self.use_custom_greeting = use_custom_greeting
        self.custom_greeting_file = "data/custom/my_greeting.wav"
        
        # Sequential greetings option
        self.use_sequential_greetings = use_sequential_greetings
        self.default_greeting_file = "data/custom/default_greeting.wav"
        self.greeting_files = {}
        
        # Scan for encounter-specific greeting files
        if self.use_sequential_greetings:
            self._load_sequential_greeting_files()
            
        # List of available greeting sounds
        self.greeting_sounds = {}
        self.current_language = "English"
        
        # Face recognition counter for the day
        self.today = datetime.datetime.now().strftime("%Y%m%d")
        
        # Individual face greeting counters
        self.face_greeting_counts = self.load_face_counts()
        
        # Total greeting count for the day
        self.daily_greeting_count = sum(self.face_greeting_counts.values())
        
        # Create greeting sound files for all languages
        self._create_greeting_sounds()
        
        # Load the default greeting sound
        try:
            if self.use_sequential_greetings and os.path.exists(self.default_greeting_file):
                pygame.mixer.music.load(self.default_greeting_file)
                logger.info(f"Using sequential greetings with default: {self.default_greeting_file}")
            elif self.use_custom_greeting and os.path.exists(self.custom_greeting_file):
                pygame.mixer.music.load(self.custom_greeting_file)
                logger.info(f"Using custom greeting from: {self.custom_greeting_file}")
            else:
                pygame.mixer.music.load(self.greeting_sounds[self.current_language])
                if self.use_custom_greeting:
                    logger.warning("Custom greeting requested but file not found. Using default greetings.")
                if self.use_sequential_greetings:
                    logger.warning("Sequential greetings requested but default file not found. Using language greetings.")
        except Exception as e:
            logger.error(f"Failed to load greeting sound: {str(e)}")
        
        logger.info("Face Detection App initialized")
        logger.info(f"Daily greeting count so far: {self.daily_greeting_count}")
        logger.info(f"Individual face counts: {dict(self.face_greeting_counts)}")
        
        if self.use_sequential_greetings:
            logger.info(f"Available encounter greetings: {list(self.greeting_files.keys())}")
    
    def _load_sequential_greeting_files(self):
        """Load all available encounter-specific greeting files"""
        greeting_path = "data/custom/greetings/greeting_*.wav"
        for file_path in glob.glob(greeting_path):
            try:
                # Extract the encounter number from the filename
                filename = os.path.basename(file_path)
                encounter_num = int(filename.split("_")[1].split(".")[0])
                self.greeting_files[encounter_num] = file_path
                logger.info(f"Loaded greeting for encounter #{encounter_num}: {file_path}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping invalid greeting file: {file_path} - {str(e)}")
        
        # Check if we have the default greeting
        if os.path.exists(self.default_greeting_file):
            logger.info(f"Default greeting file found: {self.default_greeting_file}")
        else:
            logger.warning("No default greeting file found. Will use language greetings as fallback.")
    
    def load_face_counts(self):
        """Load the face greeting counts from a JSON file"""
        stats_file = f"data/stats/stats_{self.today}.json"
        
        # Initialize with defaultdict for easy counting
        face_counts = defaultdict(int)
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    if 'face_counts' in stats and isinstance(stats['face_counts'], dict):
                        # Convert string keys back to defaultdict
                        for face_id, count in stats['face_counts'].items():
                            face_counts[face_id] = count
                    logger.info(f"Loaded face counts from {stats_file}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Failed to load face stats: {e}. Starting with empty counts.")
        else:
            logger.info(f"No previous stats for today. Starting with empty counts.")
        
        return face_counts
    
    def save_face_counts(self):
        """Save the face greeting counts to a JSON file"""
        stats_file = f"data/stats/stats_{self.today}.json"
        
        try:
            # Convert defaultdict to regular dict for JSON serialization
            stats = {
                'greeting_count': self.daily_greeting_count,
                'face_counts': dict(self.face_greeting_counts)
            }
            with open(stats_file, 'w') as f:
                json.dump(stats, f)
            logger.info(f"Saved face greeting counts to {stats_file}")
        except Exception as e:
            logger.error(f"Failed to save face stats: {str(e)}")
    
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
    
    def _create_greeting_sounds(self):
        """Create greeting sound files for all languages using espeak (if available)"""
        for language, greeting in GREETINGS.items():
            sound_file = f"data/audio/hello_{language.lower()}.wav"
            self.greeting_sounds[language] = sound_file
            
            # Skip if the file already exists
            if os.path.exists(sound_file):
                continue
                
            try:
                # Get voice parameters for this language or use default
                voice_params = VOICE_PARAMS.get(language, VOICE_PARAMS['default'])
                
                # Use espeak to create an audio file with better parameters for more natural voice
                cmd = f"espeak {voice_params} -w {sound_file} \"{greeting}\""
                subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                logger.info(f"Created greeting sound file for {language}: {sound_file}")
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.error(f"Failed to create greeting sound for {language}: {str(e)}")
                # Create an empty file so we don't keep trying to create it
                Path(sound_file).touch()
    
    def speak(self, face_id, encounter_count=0):
        """Play a greeting sound based on encounter count"""
        try:
            # Check if music is currently playing
            if not pygame.mixer.music.get_busy():
                if self.use_sequential_greetings:
                    # Use encounter-specific greeting if available
                    greeting_file = None
                    greeting_text = None
                    
                    # Try to get the specific greeting for this encounter count
                    if encounter_count in self.greeting_files:
                        greeting_file = self.greeting_files[encounter_count]
                        greeting_text = f"Encounter #{encounter_count} greeting"
                    # Fall back to default greeting if available
                    elif os.path.exists(self.default_greeting_file):
                        greeting_file = self.default_greeting_file
                        greeting_text = "Default greeting"
                    # Fall back to language greeting as last resort
                    else:
                        self.current_language = random.choice(list(GREETINGS.keys()))
                        greeting_file = self.greeting_sounds[self.current_language]
                        greeting_text = f"{GREETINGS[self.current_language]} ({self.current_language})"
                    
                    # Load and play the selected greeting
                    pygame.mixer.music.load(greeting_file)
                    pygame.mixer.music.play()
                    logger.info(f"Played {greeting_text} for face {face_id} (encounter #{encounter_count})")
                    
                elif self.use_custom_greeting and os.path.exists(self.custom_greeting_file):
                    # Use custom greeting
                    pygame.mixer.music.load(self.custom_greeting_file)
                    pygame.mixer.music.play()
                    logger.info("Played custom greeting")
                else:
                    # Select a random language
                    self.current_language = random.choice(list(GREETINGS.keys()))
                    greeting_file = self.greeting_sounds[self.current_language]
                    
                    # Load and play the greeting in the selected language
                    pygame.mixer.music.load(greeting_file)
                    pygame.mixer.music.play()
                    logger.info(f"Played greeting in {self.current_language}: {GREETINGS[self.current_language]}")
                
                # Update the last global greeting time
                self.last_global_greeting_time = time.time()
                
                # Increment counter for this specific face
                self.face_greeting_counts[face_id] += 1
                
                # Update total daily count
                self.daily_greeting_count = sum(self.face_greeting_counts.values())
                
                logger.info(f"Face {face_id} greeted {self.face_greeting_counts[face_id]} times today")
                logger.info(f"Total greeting count for today: {self.daily_greeting_count}")
                
                # Save the updated counts
                self.save_face_counts()
                
                return True
        except Exception as e:
            logger.error(f"Failed to play sound: {str(e)}")
            return False
        
        return False
    
    def update_tracked_faces(self, detected_faces, frame):
        """Update the list of tracked faces based on new detections"""
        # Increment missing frames count for all current faces
        for face in self.tracked_faces:
            face.frames_missing += 1
        
        # Process new detections
        matched_indices = []
        
        # For each detected face
        for x, y, w, h in detected_faces:
            matched = False
            
            # Try to match with existing faces
            for i, face in enumerate(self.tracked_faces):
                distance = face.distance_to(x, y, w, h)
                
                if distance < self.same_face_threshold:
                    # Update the existing face position
                    face.update_position(x, y, w, h)
                    matched = True
                    matched_indices.append(i)
                    break
            
            # If no match found, add as a new face
            if not matched:
                new_face = TrackedFace(x, y, w, h)
                self.tracked_faces.append(new_face)
                
                # Save a photo of the new face
                self.save_face_photo(frame, new_face)
        
        # Remove faces that haven't been seen for a while
        self.tracked_faces = [face for face in self.tracked_faces if face.frames_missing < self.max_missing_frames]
    
    def save_face_photo(self, frame, face):
        """Save a photo of the detected face"""
        try:
            # Create a timestamp for the filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create the filename with face ID
            filename = f"data/photos/{face.id}_{timestamp}.jpg"
            
            # Extract the face region with some margin
            margin = 20  # pixels of margin around the face
            y1 = max(0, face.y - margin)
            y2 = min(frame.shape[0], face.y + face.h + margin)
            x1 = max(0, face.x - margin)
            x2 = min(frame.shape[1], face.x + face.w + margin)
            
            face_img = frame[y1:y2, x1:x2]
            
            # Save the face image
            cv2.imwrite(filename, face_img)
            
            # Set file permissions to be readable by anyone (0o644 = rw-r--r--)
            os.chmod(filename, 0o644)
            
            # Add to set of saved faces
            self.saved_face_photos.add(face.id)
            
            logger.info(f"Saved photo of face {face.id} to {filename}")
        except Exception as e:
            logger.error(f"Failed to save face photo: {str(e)}")
    
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
        
        # Update tracked faces based on new detections
        self.update_tracked_faces(faces, frame)
        
        # Get current time for cooldown checks
        current_time = time.time()
        
        # Check global cooldown
        global_cooldown_active = (current_time - self.last_global_greeting_time) < self.global_greeting_cooldown
        if global_cooldown_active:
            # Add a small indicator that cooldown is active
            cv2.putText(frame, "Cooldown active", (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw the daily greeting count at the top of the frame
        cv2.putText(frame, f"Total Faces Greeted Today: {self.daily_greeting_count}", 
                  (frame.shape[1] - 350, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Process tracked faces
        for face in self.tracked_faces:
            # Skip faces that are missing in the current frame
            if face.frames_missing > 0:
                continue
                
            # Draw a rectangle around the face
            cv2.rectangle(frame, (face.x, face.y), (face.x + face.w, face.y + face.h), (0, 255, 0), 2)
            
            # Get individual greeting count for this face
            face_greeting_count = self.face_greeting_counts.get(face.id, 0)
            
            # Display the persistent face ID and greeting count
            cv2.putText(frame, f"ID: {face.id}", (face.x, face.y - 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Display the number of times this face has been greeted
            cv2.putText(frame, f"Greeted: {face_greeting_count}", (face.x, face.y + face.h + 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Log the detection
            logger.info(f"Face {face.id} detected at coordinates: x={face.x}, y={face.y}, w={face.w}, h={face.h}")
            
            # Check if face is on cooldown
            cooldown_active = (current_time - face.last_greeting_time) < self.greeting_cooldown
            if cooldown_active:
                cooldown_remaining = round(self.greeting_cooldown - (current_time - face.last_greeting_time))
                cv2.putText(frame, f"Cooldown: {cooldown_remaining}s", (face.x, face.y + face.h + 50), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Check if we should greet this face (based on both face-specific and global cooldowns)
            if not cooldown_active and not global_cooldown_active:
                # Determine encounter number for sequential greetings
                if self.use_sequential_greetings:
                    # Increment encounter count before greeting
                    face.encounter_count += 1
                    encounter_num = face.encounter_count
                    
                    # Only update the face cooldown if a greeting was actually played
                    if self.speak(face.id, encounter_num):
                        face.last_greeting_time = current_time
                        
                        # Determine greeting text to display
                        if encounter_num in self.greeting_files:
                            greeting_text = f"Encounter #{encounter_num} greeting"
                        elif os.path.exists(self.default_greeting_file):
                            greeting_text = f"Default greeting (encounter #{encounter_num})"
                        else:
                            greeting_text = f"{GREETINGS[self.current_language]} ({self.current_language})"
                        
                        cv2.putText(frame, greeting_text, (face.x, face.y - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        logger.info(f"Sequential greeting #{encounter_num} played for face {face.id}")
                else:
                    # Only update the face cooldown if a greeting was actually played
                    if self.speak(face.id):
                        face.last_greeting_time = current_time
                        
                        # Display the greeting text on the frame
                        if self.use_custom_greeting and os.path.exists(self.custom_greeting_file):
                            greeting_text = "Custom Greeting"
                        else:
                            greeting_text = f"{GREETINGS[self.current_language]} ({self.current_language})"
                        
                        cv2.putText(frame, greeting_text, (face.x, face.y - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        if self.use_custom_greeting:
                            logger.info(f"Custom greeting played for face {face.id}")
                        else:
                            logger.info(f"Greeting sent in {self.current_language} for face {face.id}")
        
        return frame
    
    def run(self):
        """Main application loop"""
        logger.info("Starting face detection loop")
        logger.info(f"Starting with {self.daily_greeting_count} total faces greeted today")
        
        try:
            while True:
                # Check if date has changed - reset counter if needed
                current_date = datetime.datetime.now().strftime("%Y%m%d")
                if current_date != self.today:
                    logger.info(f"New day detected. Resetting counter from {self.daily_greeting_count} to 0")
                    self.today = current_date
                    self.face_greeting_counts = defaultdict(int)
                    self.daily_greeting_count = 0
                    # Reset the TrackedFace ID counter
                    TrackedFace.next_id = 1
                    self.tracked_faces = []
                    self.save_face_counts()
                
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
                
                # Display mode info
                if self.use_sequential_greetings:
                    mode_text = "Mode: Sequential Greetings"
                elif self.use_custom_greeting:
                    mode_text = "Mode: Custom Greeting"
                else:
                    mode_text = "Mode: Random Languages"
                cv2.putText(processed_frame, mode_text, (10, 20),
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
            # Save the final count before closing
            self.save_face_counts()
            
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
    print("\nTo use your custom greeting:")
    print("python main.py --custom-greeting")

if __name__ == "__main__":
    try:
        if args.list_cameras:
            list_available_cameras()
        else:
            # Check for sequential greetings option
            if args.sequential_greetings:
                # Check if default greeting file exists
                default_file = "data/custom/default_greeting.wav"
                greeting_dir = "data/custom/greetings"
                
                if not os.path.exists(greeting_dir) or len(os.listdir(greeting_dir)) == 0:
                    if not os.path.exists(default_file):
                        print("No sequential greeting files found. Please run setup.py first to record your greetings.")
                        print("Continuing with language greetings as fallback...")
                
                print("Using sequential greetings mode")
                app = FaceDetectionApp(args.camera, False, True)
            # Check if custom greeting file exists and add a note if using it
            elif args.custom_greeting:
                custom_file = "data/custom/my_greeting.wav"
                if os.path.exists(custom_file):
                    print("Using custom greeting recording")
                else:
                    print("Custom greeting file not found. Please run setup.py first to record your greeting.")
                
                app = FaceDetectionApp(args.camera, args.custom_greeting, False)
            else:
                app = FaceDetectionApp(args.camera, False, False)
                
            app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Error: {str(e)}")
        print("To list available cameras, run: python main.py --list-cameras")
