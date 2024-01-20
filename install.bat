@echo off

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please download and install it from https://www.python.org/downloads/ based on your operating system.
    exit /b 1
) else (
    echo Python is already installed.
)

:: Get the current directory
set "PROJECT_DIR=%~dp0"

:: Navigate to the project directory
cd /d "%PROJECT_DIR%" || (
    echo Failed to navigate to the project directory.
    exit /b 1
)

:: Check if virtual environment exists, if not, create one
if not exist "venv" (
    echo Creating a virtual environment...
    python -m venv venv || (
        echo Failed to create a virtual environment.
        exit /b 1
    )
    echo Virtual environment 'venv' created successfully.
)

:: Activate the virtual environment
echo Activating the virtual environment...
call venv\Scripts\activate || (
    echo Failed to activate the virtual environment.
    exit /b 1
)
echo Virtual environment activated successfully.

:: Install dependencies
echo Installing required dependencies...
pip install -r requirements.txt || (
    echo Failed to install dependencies.
    exit /b 1
)
echo Dependencies installed successfully.

echo Setup completed successfully.
