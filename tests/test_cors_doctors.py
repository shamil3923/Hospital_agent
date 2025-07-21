#!/usr/bin/env python3
"""
Test CORS for Doctors API
"""

import requests

def test_cors_doctors():
    print('=== TESTING CORS FOR DOCTORS API ===')
    
    # Test CORS by making the same request the frontend would make
    headers = {
        'Origin': 'http://localhost:3001',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get('http://localhost:8000/api/doctors', headers=headers)
        print(f'Status: {response.status_code}')
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        print(f'CORS Headers: {cors_headers}')
        
        if response.status_code == 200:
            data = response.json()
            doctors_count = len(data.get('doctors', []))
            print(f'Doctors count: {doctors_count}')
            
            if doctors_count > 0:
                print('✅ API is working and returning doctors')
            else:
                print('⚠️ API working but no doctors found')
        else:
            print(f'❌ API Error: {response.text}')
            
    except Exception as e:
        print(f'❌ Request failed: {e}')

    print('=== CORS TEST COMPLETED ===')

if __name__ == "__main__":
    test_cors_doctors()
