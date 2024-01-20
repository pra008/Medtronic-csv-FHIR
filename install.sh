#!/bin/bash

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo "Python is already installed."
else
    echo "Python is not installed. Please download and install it from https://www.python.org/downloads/ based on your operating system."
    exit 1
fi

# Get the current directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"

# Navigate to the project directory
cd "$PROJECT_DIR" || { echo "Failed to navigate to the project directory."; exit 1; }

# Check if virtual environment exists, if not, create one
if [ ! -d "venv" ]; then
    echo "Creating a virtual environment..."
    python3 -m venv venv || { echo "Failed to create a virtual environment."; exit 1; }
    echo "Virtual environment 'venv' created successfully."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate || { echo "Failed to activate the virtual environment."; exit 1; }
echo "Virtual environment activated successfully."

# Install dependencies
echo "Installing required dependencies..."
pip install -r requirements.txt || { echo "Failed to install dependencies."; exit 1; }
echo "Dependencies installed successfully."

echo "Setup completed successfully."
