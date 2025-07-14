"""
Restart frontend with proper styling
"""
import subprocess
import os
import sys
import time

def restart_frontend():
    """Restart the frontend with clean build"""
    print("🎨 Restarting frontend with proper styling...")
    
    frontend_dir = "frontend"
    
    try:
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        # Clean install dependencies
        print("📦 Cleaning and reinstalling dependencies...")
        subprocess.run(["npm", "install"], check=True)
        
        # Start dev server
        print("🚀 Starting development server...")
        subprocess.run(["npm", "run", "dev"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
        return True
    
    return True

if __name__ == "__main__":
    restart_frontend()
