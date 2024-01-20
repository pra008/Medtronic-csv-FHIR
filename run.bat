REM Run your Python script
echo Running Python script...
python main.py
if %errorlevel% neq 0 (
    echo Failed to run Python script.
    exit /b 1
)

echo Python script finished running successfully.
exit /b 0