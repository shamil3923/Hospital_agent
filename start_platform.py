"""
Hospital Agent Platform Startup Script
"""
import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🏥 Hospital Operations & Logistics Platform           ║
    ║                                                              ║
    ║        Powered by LangGraph + MCP + Gemini AI               ║
    ║        🔧 MCP Server Integration Enabled                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if all requirements are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import langchain
        import langgraph
        import chromadb
        print("✅ Backend dependencies installed")
    except ImportError as e:
        print(f"❌ Missing backend dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    # Check if frontend dependencies exist
    frontend_path = Path("frontend")
    if not (frontend_path / "node_modules").exists():
        print("❌ Frontend dependencies not installed")
        print("Please run: cd frontend && npm install")
        return False
    
    print("✅ Frontend dependencies installed")
    return True

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
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
    print("🗄️  Initializing database...")
    
    try:
        # Run the data initialization script
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
    
    try:
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=os.getcwd())
        
        print("✅ Backend server starting on http://localhost:8000")
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None


def start_mcp_server():
    """Start the MCP server"""
    print("🔧 Starting MCP server...")

    try:
        # Start MCP server process
        mcp_server_path = Path(__file__).parent / "hospital_mcp" / "server.py"
        if not mcp_server_path.exists():
            print("⚠️  MCP server script not found, skipping MCP server startup")
            return None

        process = subprocess.Popen([
            sys.executable, str(mcp_server_path)
        ], cwd=os.getcwd(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

        print("✅ MCP server starting")
        return process
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return None

def start_frontend():
    """Start the React frontend"""
    print("🎨 Starting frontend server...")
    
    try:
        # Start npm dev server
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd="frontend")
        
        print("✅ Frontend server starting on http://localhost:3000")
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def wait_for_servers():
    """Wait for servers to be ready"""
    print("⏳ Waiting for servers to start...")
    
    import requests
    import time
    
    # Wait for backend
    backend_ready = False
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=1)
            if response.status_code == 200:
                backend_ready = True
                break
        except:
            pass
        time.sleep(1)
    
    if backend_ready:
        print("✅ Backend server is ready")
    else:
        print("⚠️  Backend server may not be ready")
    
    # Wait a bit more for frontend
    time.sleep(5)
    print("✅ Frontend server should be ready")

def open_browser():
    """Open browser to the application"""
    print("🌐 Opening browser...")
    
    import webbrowser
    try:
        webbrowser.open("http://localhost:3000")
        print("✅ Browser opened to http://localhost:3000")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please open http://localhost:3000 manually")

def main():
    """Main startup function"""
    print_banner()
    
    # Store process references for cleanup
    processes = []
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down servers...")
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ Servers stopped")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Pre-flight checks
        if not check_requirements():
            return 1
        
        if not setup_environment():
            return 1
        
        # Initialize database
        if not initialize_database():
            return 1
        
        # Start servers
        backend_process = start_backend()
        if not backend_process:
            return 1
        processes.append(backend_process)

        # Start MCP server
        mcp_process = start_mcp_server()
        if mcp_process:
            processes.append(mcp_process)

        frontend_process = start_frontend()
        if not frontend_process:
            return 1
        processes.append(frontend_process)
        
        # Wait for servers to be ready
        wait_for_servers()
        
        # Open browser
        open_browser()
        
        print("\n" + "="*60)
        print("🎉 Hospital Agent Platform is running!")
        print("="*60)
        print("📊 Dashboard: http://localhost:3000")
        print("🔗 API Docs: http://localhost:8000/docs")
        print("🔧 MCP Server: Running (stdio communication)")
        print("💬 Chat with the Bed Management Agent in the web interface")
        print("\nPress Ctrl+C to stop all servers")
        print("="*60)
        
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            for process in processes:
                if process.poll() is not None:
                    print(f"⚠️  A server process has stopped unexpectedly")
                    return 1
    
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
