"""
Test LLM and Backend Connection
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test Gemini API connection"""
    print("🤖 Testing Gemini API connection...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.1
        )
        
        # Test simple query
        response = llm.invoke("Hello, can you respond with 'LLM connection successful'?")
        print(f"✅ LLM Response: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🗄️ Testing database connection...")
    
    try:
        from backend.database import SessionLocal, Bed
        
        db = SessionLocal()
        bed_count = db.query(Bed).count()
        db.close()
        
        print(f"✅ Database connected. Beds in database: {bed_count}")
        return True
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

def test_agent_system():
    """Test the bed management agent"""
    print("🏥 Testing bed management agent...")
    
    try:
        from agents.bed_management.agent import bed_management_agent
        
        # Test agent query
        result = bed_management_agent.process_query("What is the current bed occupancy?")
        
        if result and "response" in result:
            print(f"✅ Agent Response: {result['response'][:100]}...")
            return True
        else:
            print("❌ Agent not responding properly")
            return False
            
    except Exception as e:
        print(f"❌ Agent Error: {e}")
        return False

def test_backend_api():
    """Test backend API endpoints"""
    print("🔗 Testing backend API...")
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
            return True
        else:
            print(f"❌ Backend API returned status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend API is not running. Start it with: uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Hospital Agent Platform - LLM & Backend Test")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Gemini LLM Connection", test_gemini_connection),
        ("Backend API", test_backend_api),
        ("Agent System", test_agent_system),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems working! Chat interface should work properly.")
        print("\nTo use the chat:")
        print("1. Make sure backend is running: uvicorn backend.main:app --reload")
        print("2. Open frontend: http://localhost:3000")
        print("3. Click 'Chat Interface' in sidebar")
        print("4. Ask: 'What is the current bed occupancy?'")
    else:
        print("❌ Some systems failed. Fix the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
