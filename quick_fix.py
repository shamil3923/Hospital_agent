"""
Quick Fix for Hospital Agent Platform
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_env_file():
    """Setup .env file with SQLite"""
    print("Setting up .env file...")
    
    env_content = """# Application Configuration
APP_NAME="Hospital Operations & Logistics Agentic Platform"
VERSION="1.0.0"
DEBUG=true
HOST="0.0.0.0"
PORT=8000

# Database Configuration (SQLite)
DATABASE_URL="sqlite:///./hospital.db"

# Security Configuration
SECRET_KEY="your-secret-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_HOSTS="http://localhost:3000,http://127.0.0.1:3000"

# LLM Configuration - Google Gemini
GOOGLE_API_KEY="AIzaSyCrEfICW4RYyJW45Uy0ZSduXVKUKjNu25I"
LLM_MODEL="gemini-2.0-flash-exp"
LLM_PROVIDER="google"

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY="./data/chroma_db"

# Agent Configuration
MAX_AGENT_RETRIES=3
AGENT_TIMEOUT=30

# Logging Configuration
LOG_LEVEL="INFO"
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(".env file created with SQLite configuration")

def install_core_packages():
    """Install only essential packages"""
    print("Installing core packages...")
    
    core_packages = [
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pydantic",
        "pydantic-settings",
        "langchain",
        "langchain-google-genai",
        "langgraph",
        "python-dotenv",
        "pandas",
        "numpy",
        "httpx"
    ]
    
    try:
        for package in core_packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
        
        print("Core packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False

def create_simple_database():
    """Create simple SQLite database"""
    print("Creating SQLite database...")

    try:
        subprocess.run([sys.executable, "create_simple_db.py"], check=True)
        print("Database created successfully")
        return True
    except Exception as e:
        print(f"Database creation error: {e}")
        return False

def create_simple_agent():
    """Create simplified agent without complex dependencies"""
    print("Creating simplified agent...")
    
    simple_agent = '''"""
Simplified Bed Management Agent
"""
from datetime import datetime
import sqlite3
import json

class SimpleBedAgent:
    def __init__(self):
        self.db_path = "hospital.db"
    
    def get_bed_occupancy(self):
        """Get bed occupancy statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM beds")
            total_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'occupied'")
            occupied_beds = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'vacant'")
            vacant_beds = cursor.fetchone()[0]
            
            conn.close()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            return {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "occupancy_rate": round(occupancy_rate, 1)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def process_query(self, query):
        """Process user query"""
        query_lower = query.lower()
        
        if "occupancy" in query_lower or "status" in query_lower:
            data = self.get_bed_occupancy()
            if "error" in data:
                response = f"Sorry, I encountered an error: {data['error']}"
            else:
                response = f"Current bed occupancy is {data['occupancy_rate']}% with {data['occupied_beds']} occupied beds out of {data['total_beds']} total beds. {data['vacant_beds']} beds are available."
        
        elif "available" in query_lower or "vacant" in query_lower:
            data = self.get_bed_occupancy()
            if "error" in data:
                response = f"Sorry, I encountered an error: {data['error']}"
            else:
                response = f"There are {data['vacant_beds']} available beds out of {data['total_beds']} total beds."
        
        else:
            response = "I'm the Bed Management Agent. I can help you with bed occupancy and availability. Try asking: 'What is the current bed occupancy?' or 'How many beds are available?'"
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "agent": "simple_bed_agent"
        }

# Global instance
simple_bed_agent = SimpleBedAgent()
'''
    
    # Create simplified agent file
    agent_dir = Path("agents/bed_management")
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    with open(agent_dir / "simple_agent.py", "w") as f:
        f.write(simple_agent)
    
    print("Simplified agent created")

def main():
    """Main fix function"""
    print("Hospital Agent Platform - Quick Fix")
    print("=" * 50)
    
    # Setup environment
    setup_env_file()
    
    # Install core packages
    if not install_core_packages():
        return 1
    
    # Create database
    if not create_simple_database():
        return 1
    
    # Create simple agent
    create_simple_agent()
    
    print("\n" + "=" * 50)
    print("Quick fix completed!")
    print("\nNext steps:")
    print("1. Test: python test_simple.py")
    print("2. Start backend: uvicorn backend.main:app --reload")
    print("3. Start frontend: cd frontend && npm run dev")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

