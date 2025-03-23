#!/usr/bin/env python3
"""
Voice Recording Module for Face Recognition System
-------------------------------------------------
This script allows you to record voice samples that can be played
when faces are detected by the main application.
"""

import os
import sys
import wave
import pyaudio
import argparse
import numpy as np
from pathlib import Path

# Constants for audio recording
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 3

def record_voice(output_file, duration=RECORD_SECONDS):
    """Record audio from microphone and save to output_file"""
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    print(f"Recording {duration} seconds of audio...")
    print("Speak now...")
    
    # Open stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    # Start recording
    frames = []
    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
        
        # Show progress
        sys.stdout.write(f"\rRecording: {i/(RATE/CHUNK*duration)*100:.1f}% complete")
        sys.stdout.flush()
    
    print("\nFinished recording!")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded data as a WAV file
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"Audio saved to {output_file}")
    return output_file

def list_recordings():
    """List all recorded voice samples"""
    audio_dir = Path("data/audio")
    if not audio_dir.exists():
        print("No recordings found. Voice sample directory doesn't exist.")
        return
    
    custom_recordings = list(audio_dir.glob("custom_*.wav"))
    
    if not custom_recordings:
        print("No custom voice recordings found.")
        return
    
    print("\nAvailable custom voice recordings:")
    for i, recording in enumerate(custom_recordings, 1):
        print(f"{i}. {recording.name}")

def main():
    parser = argparse.ArgumentParser(description='Voice Recording Tool')
    parser.add_argument('--record', action='store_true', help='Record a new voice sample')
    parser.add_argument('--name', type=str, help='Name for the voice recording (used as file name)')
    parser.add_argument('--duration', type=int, default=RECORD_SECONDS, 
                        help=f'Recording duration in seconds (default: {RECORD_SECONDS})')
    parser.add_argument('--list', action='store_true', help='List available voice recordings')
    
    args = parser.parse_args()
    
    # Create audio directory if it doesn't exist
    os.makedirs("data/audio", exist_ok=True)
    
    if args.list:
        list_recordings()
        return
    
    if args.record:
        if not args.name:
            print("Please provide a name for the recording using --name")
            return
            
        # Sanitize the filename
        safe_name = ''.join(c if c.isalnum() else '_' for c in args.name.lower())
        output_file = f"data/audio/custom_{safe_name}.wav"
        
        # Check if PyAudio is available
        try:
            p = pyaudio.PyAudio()
            p.terminate()
        except Exception as e:
            print(f"Error initializing PyAudio: {str(e)}")
            print("Make sure PyAudio is installed: pip install pyaudio")
            return
            
        # Record the voice
        record_voice(output_file, duration=args.duration)
        print(f"\nRecording completed! You can use this recording in the face recognition system.")
        print(f"To use this recording, run the main app with: python main.py --custom-voice={safe_name}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 