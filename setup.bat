@echo off
echo 🏥 HOSPITAL AGENT - SETUP SCRIPT
echo ========================================
echo Setting up Hospital Management System
echo.

echo 🐍 Step 1: Creating Python Virtual Environment...
python -m venv hospital_env
if errorlevel 1 (
    echo ❌ Error: Python not found or failed to create virtual environment
    echo Please ensure Python 3.8+ is installed and in your PATH
    pause
    exit /b 1
)

echo.
echo 🚀 Step 2: Activating Virtual Environment...
call hospital_env\Scripts\activate.bat

echo.
echo 📦 Step 3: Installing Python Dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo 🌐 Step 4: Installing Frontend Dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo ❌ Error: Failed to install frontend dependencies
    echo Please ensure Node.js and npm are installed
    pause
    exit /b 1
)

cd ..

echo.
echo ✅ SETUP COMPLETE!
echo ========================================
echo.
echo 🎉 Hospital Agent is ready to use!
echo.
echo To start the system:
echo   1. Run: start_hospital_system.bat
echo   2. Wait for both servers to start
echo   3. Open http://localhost:5173 in your browser
echo.
echo Press any key to exit...
pause > nul
