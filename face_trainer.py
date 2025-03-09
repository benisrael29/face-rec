#!/usr/bin/env python3
"""
Face Training Utility
--------------------
This script allows you to train the face recognition system to identify
specific people by name. It captures images of a person's face and
saves their facial encoding for later recognition.
"""

import os
import cv2
import time
import pickle
import numpy as np
import face_recognition
from datetime import datetime

# Create directories if they don't exist
os.makedirs('data/trained_faces', exist_ok=True)
os.makedirs('data/face_images', exist_ok=True)

# Path to save encodings
ENCODINGS_FILE = 'data/trained_faces/encodings.pkl'

def load_encodings():
    """Load existing encodings if available"""
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, 'rb') as f:
            return pickle.load(f)
    return {'names': [], 'encodings': []}

def save_encodings(data):
    """Save encodings to disk"""
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(data, f)
    print(f"Encodings saved to {ENCODINGS_FILE}")

def capture_face(name):
    """Capture and process face images for the given name"""
    print(f"\nTraining system to recognize {name}...")
    print("Position your face in front of the camera.")
    
    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return False
    
    # Set camera resolution
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    face_encodings = []
    num_samples = 5
    current_sample = 0
    
    try:
        while current_sample < num_samples:
            # Capture frame
            ret, frame = camera.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break
            
            # Display countdown
            sample_text = f"Sample: {current_sample+1}/{num_samples}"
            cv2.putText(frame, sample_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Show the frame
            cv2.imshow('Capture Face', frame)
            key = cv2.waitKey(1)
            
            # Capture sample on spacebar press
            if key == 32:  # Spacebar
                # Find face locations
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if not face_locations:
                    print("No face detected. Please position your face properly.")
                    continue
                
                # Use the first face found
                top, right, bottom, left = face_locations[0]
                face_image = frame[top:bottom, left:right]
                
                # Save face image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"data/face_images/{name}_{timestamp}_{current_sample}.jpg"
                cv2.imwrite(image_path, face_image)
                
                # Get face encoding
                encodings = face_recognition.face_encodings(rgb_frame, [face_locations[0]])
                if encodings:
                    face_encodings.append(encodings[0])
                    current_sample += 1
                    print(f"Sample {current_sample}/{num_samples} captured")
                    
                    # Add a short delay to allow user to reposition
                    time.sleep(1)
                else:
                    print("Could not encode face. Please try again.")
                
            # Press 'q' to quit
            elif key == ord('q'):
                return False
    
    finally:
        camera.release()
        cv2.destroyAllWindows()
    
    # If we collected all samples
    if len(face_encodings) == num_samples:
        # Load existing encodings
        data = load_encodings()
        
        # Add new encodings
        for encoding in face_encodings:
            data['names'].append(name)
            data['encodings'].append(encoding)
        
        # Save updated encodings
        save_encodings(data)
        print(f"Successfully trained system to recognize {name}!")
        return True
    
    print("Training incomplete. Please try again.")
    return False

def list_known_faces():
    """List all people the system has been trained to recognize"""
    data = load_encodings()
    if not data['names']:
        print("No faces have been trained yet.")
        return
    
    # Count unique names
    unique_names = {}
    for name in data['names']:
        if name in unique_names:
            unique_names[name] += 1
        else:
            unique_names[name] = 1
    
    print("\nTrained Faces:")
    print("-------------")
    for name, count in unique_names.items():
        print(f"- {name}: {count} samples")

def main():
    print("Face Recognition Trainer")
    print("=======================")
    
    while True:
        print("\nOptions:")
        print("1. Add a new face")
        print("2. List known faces")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            name = input("Enter the person's name: ")
            if name:
                capture_face(name)
            else:
                print("Name cannot be empty.")
        
        elif choice == '2':
            list_known_faces()
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 