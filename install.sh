#!/bin/bash

# Face Detection Application Installation Script for Xubuntu
# ---------------------------------------------------------

# Text formatting
BOLD="\e[1m"
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
RESET="\e[0m"

# Function to print section headers
print_header() {
    echo -e "\n${BOLD}$1${RESET}"
    echo -e "$(printf '=%.0s' {1..50})"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${RESET}"
}

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    print_error "This installation script is designed for Xubuntu/Linux systems."
    print_error "Current OS: $(uname)"
    exit 1
fi

print_header "Face Detection Application - Installation Script"
echo "This script will install the necessary dependencies and set up the application."

# Check for sudo privileges
print_header "Checking permissions"
if [[ $EUID -ne 0 ]]; then
    print_warning "This script requires sudo privileges to install system dependencies."
    echo "Please enter your password when prompted."
    
    # Check if sudo is available
    if ! command -v sudo &> /dev/null; then
        print_error "sudo command not found. Please run this script as root or install sudo."
        exit 1
    fi
else
    print_success "Running with administrator privileges."
fi

# Install system dependencies
print_header "Installing system dependencies"
echo "This may take a few minutes..."

# Function to run apt commands with error handling
apt_install() {
    if sudo apt-get install -y "$@"; then
        print_success "Installed: $*"
    else
        print_error "Failed to install: $*"
        echo "Please try installing manually: sudo apt-get install $*"
    fi
}

# Update package lists
echo "Updating package lists..."
if sudo apt-get update; then
    print_success "Package lists updated."
else
    print_error "Failed to update package lists."
    echo "Please try running: sudo apt-get update"
    exit 1
fi

# Install essential build dependencies
echo "Installing build essentials and development libraries..."
apt_install python3-dev python3-pip python3-venv
apt_install espeak

# Install SDL libraries for pygame
echo "Installing SDL libraries for audio playback..."
apt_install libsdl2-dev libsdl2-mixer-2.0-0

# Install libraries for sounddevice and soundfile
echo "Installing libraries for audio recording..."
apt_install libsndfile1-dev

# Set up Python virtual environment
print_header "Setting up Python virtual environment"

# Create venv directory if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    if python3 -m venv venv; then
        print_success "Virtual environment created."
    else
        print_error "Failed to create virtual environment."
        exit 1
    fi
else
    print_warning "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_error "Failed to activate virtual environment."
    exit 1
else
    print_success "Virtual environment activated: $VIRTUAL_ENV"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_header "Installing Python dependencies"
echo "This may take some time for OpenCV..."

if pip install -r requirements.txt; then
    print_success "Python dependencies installed successfully."
else
    print_error "Failed to install some dependencies."
    print_warning "You may need to install some packages manually."
fi

# Create necessary directories
print_header "Setting up application directories"

# Create directories
mkdir -p logs data/audio data/custom

# Set proper permissions
chmod -R 755 logs data
print_success "Directory structure created."

# Make Python scripts executable
chmod +x main.py
print_success "Made Python scripts executable."

# Add camera and audio group permissions
print_header "Setting user permissions"
if sudo usermod -a -G video $USER; then
    print_success "Added current user to video group."
else
    print_warning "Failed to add user to video group."
    echo "You may need to run this command manually: sudo usermod -a -G video $USER"
fi

if sudo usermod -a -G audio $USER; then
    print_success "Added current user to audio group."
else
    print_warning "Failed to add user to audio group."
    echo "You may need to run this command manually: sudo usermod -a -G audio $USER"
fi

# Final instructions
print_header "Installation Complete"
echo -e "${BOLD}To use the application:${RESET}"
echo ""
echo "1. You may need to log out and log back in for group permissions to take effect."
echo ""
echo "2. Activate the virtual environment:"
echo "   $ source venv/bin/activate"
echo ""
echo "3. Run the setup script to configure your custom voice greeting:"
echo "   $ python setup.py"
echo ""
echo "4. Or run the face detection application directly:"
echo "   $ python main.py"
echo ""
echo "5. To use your custom voice greeting with the application:"
echo "   $ python main.py --custom-greeting"
echo ""
print_warning "Note: The first run might be slow as OpenCV initializes."

exit 0 