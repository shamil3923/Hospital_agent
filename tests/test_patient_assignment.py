#!/usr/bin/env python3
"""
Test Patient Assignment Functionality
"""

import requests
import json

def test_patient_assignment():
    print('=== TESTING PATIENT ASSIGNMENT VIA CHATBOT ===')
    print()

    # Test 1: General assignment inquiry
    print('1. 🤖 General Assignment Inquiry')
    try:
        response = requests.post('http://localhost:8000/api/chat', 
                                json={'message': 'I need to assign a patient'})
        result = response.json()
        print(f'Status: {response.status_code}')
        print(f'Agent: {result.get("agent", "unknown")}')
        print(f'Response preview: {result.get("response", "")[:200]}...')
    except Exception as e:
        print(f'Error: {e}')
    print()

    # Test 2: Check available beds first
    print('2. 🛏️ Check Available Beds')
    try:
        response = requests.post('http://localhost:8000/api/chat', 
                                json={'message': 'show me available beds'})
        result = response.json()
        print(f'Status: {response.status_code}')
        print(f'Response preview: {result.get("response", "")[:300]}...')
    except Exception as e:
        print(f'Error: {e}')
    print()

    # Test 3: Specific patient assignment to available bed
    print('3. 🏥 Specific Patient Assignment')
    try:
        response = requests.post('http://localhost:8000/api/chat', 
                                json={'message': 'assign John Smith to bed ER-02'})
        result = response.json()
        print(f'Status: {response.status_code}')
        print(f'Agent: {result.get("agent", "unknown")}')
        print(f'Response preview: {result.get("response", "")[:400]}...')
    except Exception as e:
        print(f'Error: {e}')
    print()

    # Test 4: Ward admission
    print('4. 🚑 Ward Admission')
    try:
        response = requests.post('http://localhost:8000/api/chat', 
                                json={'message': 'admit Sarah Johnson to Emergency'})
        result = response.json()
        print(f'Status: {response.status_code}')
        print(f'Agent: {result.get("agent", "unknown")}')
        print(f'Response preview: {result.get("response", "")[:400]}...')
    except Exception as e:
        print(f'Error: {e}')
    print()

    # Test 5: ICU assignment
    print('5. 🏥 ICU Assignment')
    try:
        response = requests.post('http://localhost:8000/api/chat', 
                                json={'message': 'assign patient to ICU'})
        result = response.json()
        print(f'Status: {response.status_code}')
        print(f'Response preview: {result.get("response", "")[:300]}...')
    except Exception as e:
        print(f'Error: {e}')
    print()

    # Test 6: Check MCP tools for assignment
    print('6. 🔧 Test MCP Assignment Tools')
    try:
        import asyncio
        from hospital_mcp.simple_client import SimpleMCPToolsManager
        
        async def test_mcp_assignment():
            manager = SimpleMCPToolsManager()
            await manager.initialize()
            
            # Test creating patient and assigning to bed
            result = await manager.execute_tool('create_patient_and_assign',
                                              patient_name='Test Patient',
                                              bed_number='GEN-02',
                                              age=35,
                                              gender='male')
            return result
        
        result = asyncio.run(test_mcp_assignment())
        print(f'MCP Assignment Result: {result.get("success", False)}')
        if result.get("success"):
            print(f'Patient: {result.get("patient_name")}')
            print(f'Bed: {result.get("bed_number")}')
            print(f'Ward: {result.get("ward")}')
        else:
            print(f'Error: {result.get("error", "Unknown error")}')
    except Exception as e:
        print(f'MCP Test Error: {e}')
    print()

    print('=== PATIENT ASSIGNMENT TESTS COMPLETED ===')

if __name__ == "__main__":
    test_patient_assignment()
