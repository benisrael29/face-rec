#!/bin/bash

echo "Face Detection Application"
echo "========================="
echo ""

# Run the setup script with Python 3
python3 setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Setup failed. Please check the error message above."
    exit 1
fi

exit 0 