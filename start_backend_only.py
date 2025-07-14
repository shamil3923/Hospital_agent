"""
Start Backend Only for Testing
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        # Copy from example
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ Created .env file from .env.example")
        else:
            print("❌ .env.example file not found")
            return False
    return True

def initialize_database():
    """Initialize database with sample data"""
    print("🗄️ Initializing database...")
    
    try:
        result = subprocess.run([
            sys.executable, "scripts/init_data.py"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend server...")
    print("Backend will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")

def main():
    """Main function"""
    print("🏥 Hospital Agent Platform - Backend Startup")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Initialize database
    if not initialize_database():
        return 1
    
    # Start backend
    start_backend()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
