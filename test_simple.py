"""
Simple Test for Hospital Agent Platform
"""
import os
import sqlite3
from datetime import datetime

def test_database():
    """Test SQLite database"""
    print("🗄️ Testing SQLite database...")
    
    try:
        conn = sqlite3.connect('hospital.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM beds")
        bed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM beds WHERE status = 'occupied'")
        occupied_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database working. Total beds: {bed_count}, Occupied: {occupied_count}")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_gemini():
    """Test Gemini API"""
    print("🤖 Testing Gemini API...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key="AIzaSyCrEfICW4RYyJW45Uy0ZSduXVKUKjNu25I",
            temperature=0.1
        )
        
        response = llm.invoke("Say 'Gemini working!'")
        print(f"✅ Gemini response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return False

def test_simple_agent():
    """Test simple agent"""
    print("🏥 Testing simple agent...")
    
    try:
        from agents.bed_management.simple_agent import simple_bed_agent
        
        result = simple_bed_agent.process_query("What is the current bed occupancy?")
        print(f"✅ Agent response: {result['response']}")
        return True
        
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return False

def main():
    """Run simple tests"""
    print("🏥 Hospital Agent Platform - Simple Test")
    print("=" * 50)
    
    tests = [
        ("SQLite Database", test_database),
        ("Gemini API", test_gemini),
        ("Simple Agent", test_simple_agent),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System is ready.")
    else:
        print("❌ Some tests failed.")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()
