#!/usr/bin/env python3
"""
Test CORS Preflight Request
"""

import requests

def test_preflight():
    print('=== TESTING CORS PREFLIGHT ===')
    
    # Test preflight request
    headers = {
        'Origin': 'http://localhost:3001',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    }

    try:
        response = requests.options('http://localhost:8000/api/doctors', headers=headers)
        print(f'Preflight Status: {response.status_code}')
        print(f'Access-Control-Allow-Origin: {response.headers.get("Access-Control-Allow-Origin")}')
        print(f'Access-Control-Allow-Methods: {response.headers.get("Access-Control-Allow-Methods")}')
        print(f'Access-Control-Allow-Headers: {response.headers.get("Access-Control-Allow-Headers")}')
        
        if response.headers.get("Access-Control-Allow-Origin"):
            print('✅ CORS is properly configured')
        else:
            print('❌ CORS headers missing')
            
    except Exception as e:
        print(f'❌ Preflight request failed: {e}')

    print('=== PREFLIGHT TEST COMPLETED ===')

if __name__ == "__main__":
    test_preflight()
