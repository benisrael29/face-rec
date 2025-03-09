#!/bin/bash

# Script to fix MacBook camera issues on Xubuntu
# ---------------------------------------------

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
    print_error "This script is designed for Xubuntu/Linux systems."
    print_error "Current OS: $(uname)"
    exit 1
fi

print_header "MacBook Camera Fix Script"
echo "This script will help diagnose and fix camera issues on MacBook hardware running Xubuntu."

# Check for sudo privileges
if [[ $EUID -ne 0 ]]; then
    print_warning "This script requires sudo privileges to fix camera issues."
    echo "Please enter your password when prompted."
    
    # Check if sudo is available
    if ! command -v sudo &> /dev/null; then
        print_error "sudo command not found. Please run this script as root or install sudo."
        exit 1
    fi
fi

# Step 1: Check for camera devices
print_header "Checking for camera devices"
echo "Looking for video devices..."

if ls /dev/video* &> /dev/null; then
    print_success "Found video devices:"
    ls -l /dev/video*
else
    print_warning "No video devices found at /dev/video*"
fi

# Check for Apple FaceTime HD camera
if ls /dev/facetime* &> /dev/null; then
    print_success "Found Apple FaceTime camera devices:"
    ls -l /dev/facetime*
else
    print_warning "No Apple FaceTime camera devices found"
fi

# Step 2: Install necessary drivers and tools
print_header "Installing necessary drivers and tools"

echo "Installing v4l2 utilities and webcam tools..."
if sudo apt-get update && sudo apt-get install -y v4l-utils guvcview cheese; then
    print_success "Installed camera utilities"
else
    print_error "Failed to install camera utilities"
fi

# Check if bcwc-pcie module is loaded (for FaceTime HD camera)
print_header "Checking for Apple camera drivers"

if lsmod | grep -q "bcwc_pcie"; then
    print_success "FaceTime HD camera driver (bcwc_pcie) is loaded"
else
    print_warning "FaceTime HD camera driver not loaded. Attempting to install..."
    
    echo "Installing dependencies for FaceTime HD camera driver..."
    sudo apt-get install -y git kmod libssl-dev checkinstall
    
    echo "Cloning and building Apple FaceTime HD driver..."
    cd /tmp
    git clone https://github.com/patjak/bcwc_pcie.git
    cd bcwc_pcie/firmware
    make
    sudo make install
    cd ..
    make
    sudo make install
    sudo depmod
    sudo modprobe -r bdc_pci
    sudo modprobe facetimehd
    
    if lsmod | grep -q "facetimehd"; then
        print_success "Successfully installed and loaded FaceTime HD camera driver"
    else
        print_error "Failed to load FaceTime HD camera driver"
    fi
fi

# Step 3: Fix permissions
print_header "Fixing camera permissions"

echo "Adding current user to video group..."
if sudo usermod -a -G video $USER; then
    print_success "Added current user to video group"
else
    print_error "Failed to add user to video group"
fi

echo "Setting permissions for video devices..."
if sudo chmod 666 /dev/video* 2>/dev/null; then
    print_success "Set permissions for video devices"
else
    print_warning "No video devices found or could not set permissions"
fi

# Step 4: Testing the camera
print_header "Testing the camera"

echo "Running v4l2-ctl to list video devices..."
v4l2-ctl --list-devices

echo "Running v4l2-ctl to check video formats..."
for dev in /dev/video*; do
    echo "Checking $dev:"
    v4l2-ctl --device=$dev --list-formats-ext
done

# Print instructions
print_header "Instructions"
echo -e "${BOLD}Important notes:${RESET}"
echo "1. You may need to log out and log back in for group permissions to take effect."
echo "2. To test the camera, you can run: cheese"
echo "3. To use our face detection app with a specific camera device:"
echo "   python main.py --camera=/dev/video0  (replace with your device path)"
echo "4. To list all available cameras:"
echo "   python main.py --list-cameras"
echo ""
print_warning "If you still have issues, try rebooting your system."

exit 0 