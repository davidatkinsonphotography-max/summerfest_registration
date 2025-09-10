@echo off
echo Starting Summerfest Registration System...
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Starting Django development server...
echo The application will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver
pause
