#!/bin/bash
# Face Recognition Voice Assistant Run Script
# This script helps record custom voices and run the face detection app

# Ensure data directories exist
mkdir -p data/audio logs

# Function to show help
show_help() {
    echo "Face Recognition Voice Assistant"
    echo "--------------------------------"
    echo "Usage: ./run.sh [option]"
    echo ""
    echo "Options:"
    echo "  --help                Show this help message"
    echo "  --record NAME         Record your voice with given name"
    echo "  --record NAME TIME    Record your voice with custom duration (seconds)"
    echo "  --list-voices         List all recorded voices"
    echo "  --list-cameras        List all available cameras"
    echo "  --use-voice NAME      Run with your recorded voice"
    echo "  --camera INDEX        Run with specific camera index"
    echo ""
    echo "Examples:"
    echo "  ./run.sh --record greeting      Record your voice as 'greeting'"
    echo "  ./run.sh --record welcome 5     Record a 5-second 'welcome' message"
    echo "  ./run.sh --use-voice greeting   Run with your 'greeting' voice"
    echo "  ./run.sh --camera 1             Run with camera at index 1"
    echo "  ./run.sh --use-voice greeting --camera 1"
    echo "                                  Run with specific voice and camera"
    echo ""
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python to run this application."
    exit 1
fi

# Check if PyAudio is installed
python -c "import pyaudio" &> /dev/null
if [ $? -ne 0 ]; then
    echo "PyAudio is not installed. Installing required dependencies..."
    
    # Check the OS and install appropriate dependencies
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Detected Linux system"
        echo "You may need to run: sudo apt-get install portaudio19-dev python3-dev"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Detected macOS system"
        echo "You may need to run: brew install portaudio"
        
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "Detected Windows system"
    fi
    
    echo "Installing PyAudio..."
    pip install pyaudio
    
    if [ $? -ne 0 ]; then
        echo "Failed to install PyAudio. Please install it manually."
        echo "For more information, see README.md"
        exit 1
    fi
fi

# Process command line arguments
CAMERA_ARG=""
VOICE_ARG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --list-voices)
            python main.py --list-voices
            exit 0
            ;;
        --list-cameras)
            python main.py --list-cameras
            exit 0
            ;;
        --record)
            if [ -z "$2" ]; then
                echo "Error: Missing name for voice recording"
                echo "Usage: ./run.sh --record NAME [DURATION]"
                exit 1
            fi
            
            VOICE_NAME=$2
            shift
            
            # Check if duration was provided
            DURATION_ARG=""
            if [[ $2 =~ ^[0-9]+$ ]]; then
                DURATION_ARG="--duration=$2"
                shift
            fi
            
            echo "Recording your voice as '$VOICE_NAME'..."
            python record_voice.py --record --name="$VOICE_NAME" $DURATION_ARG
            
            # Ask if user wants to use this voice right away
            read -p "Do you want to run the face detection with this voice now? (y/n): " USE_VOICE
            if [[ $USE_VOICE == "y" || $USE_VOICE == "Y" ]]; then
                python main.py --custom-voice="$VOICE_NAME" $CAMERA_ARG
            fi
            exit 0
            ;;
        --use-voice)
            if [ -z "$2" ]; then
                echo "Error: Missing name for voice to use"
                echo "Usage: ./run.sh --use-voice NAME"
                exit 1
            fi
            VOICE_ARG="--custom-voice=$2"
            shift
            ;;
        --camera)
            if [ -z "$2" ]; then
                echo "Error: Missing camera index"
                echo "Usage: ./run.sh --camera INDEX"
                exit 1
            fi
            CAMERA_ARG="--camera=$2"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# If no specific options were provided, just run the app
if [ -z "$VOICE_ARG" ] && [ -z "$CAMERA_ARG" ]; then
    echo "Running face detection with default settings..."
    python main.py
    exit 0
fi

# Run with the specified options
echo "Running face detection..."
python main.py $VOICE_ARG $CAMERA_ARG 