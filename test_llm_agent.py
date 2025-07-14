"""
Test LLM Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llm_agent():
    """Test the LLM-powered bed agent"""
    print("Testing LLM Bed Management Agent")
    print("=" * 40)
    
    try:
        from agents.bed_management.llm_agent import llm_bed_agent
        
        # Test queries
        test_queries = [
            "What is the current bed occupancy?",
            "How many beds are available?",
            "Can you predict the patient flow for next 5 days?",
            "Show me ICU bed status",
            "What's the status in Emergency ward?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            print("-" * 30)
            
            result = llm_bed_agent.process_query(query)
            
            print(f"Response: {result['response']}")
            print(f"Agent: {result['agent']}")
            print(f"LLM Used: {result.get('llm_used', 'Unknown')}")
            
            if 'data_used' in result:
                data = result['data_used']
                print(f"Data: {data.get('occupied_beds', 0)}/{data.get('total_beds', 0)} beds occupied")
        
        return True
        
    except Exception as e:
        print(f"Error testing LLM agent: {e}")
        return False

def test_api_endpoint():
    """Test the chat API endpoint"""
    print("\n" + "=" * 40)
    print("Testing Chat API Endpoint")
    print("=" * 40)
    
    try:
        import requests
        
        test_message = "What is the current bed occupancy?"
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": test_message},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {data['response'][:100]}...")
            print(f"Agent: {data.get('agent', 'unknown')}")
            return True
        else:
            print(f"❌ API returned status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running. Start with: uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 LLM Agent Test Suite")
    print("=" * 50)
    
    # Test 1: Direct agent test
    agent_works = test_llm_agent()
    
    # Test 2: API endpoint test
    api_works = test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"LLM Agent: {'✅ Working' if agent_works else '❌ Failed'}")
    print(f"API Endpoint: {'✅ Working' if api_works else '❌ Failed'}")
    
    if agent_works and api_works:
        print("\n🎉 All tests passed! LLM chatbot should work properly.")
        print("\nTry these in the chat interface:")
        print("- 'What is the current bed occupancy?'")
        print("- 'Can you predict patient flow for next 5 days?'")
        print("- 'Show me available ICU beds'")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
