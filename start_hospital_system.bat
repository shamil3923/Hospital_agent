@echo off
echo 🏥 HOSPITAL AGENT - SYSTEM STARTUP
echo ========================================
echo Starting Hospital Management System
echo.

echo 🚀 Step 1: Activating Virtual Environment...
call hospital_env\Scripts\activate.bat

echo.
echo 🚀 Step 2: Starting Backend Server...
echo Backend will run on: http://localhost:8001
echo.

cd backend
start "Hospital Agent Backend" cmd /k "python main.py"

echo.
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo 🖥️  Step 3: Starting Frontend Development Server...
echo Frontend will run on: http://localhost:5173
echo.

cd ..\frontend
start "Hospital Agent Frontend" cmd /k "npm run dev"

echo.
echo 🎉 HOSPITAL SYSTEM STARTING!
echo ========================================
echo Backend: http://localhost:8001
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8001/docs
echo.
echo ✅ Both systems are starting in separate windows
echo ✅ Wait 10-15 seconds for full startup
echo ✅ Then open http://localhost:5173 in your browser
echo.
echo Press any key to close this window...
pause > nul
