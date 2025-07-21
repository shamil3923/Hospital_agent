#!/usr/bin/env python3
"""
Test Doctors API Endpoint
"""

import requests
import json

def test_doctors_api():
    print('=== TESTING DOCTORS API ===')
    
    try:
        response = requests.get('http://localhost:8000/api/doctors')
        print(f'Status: {response.status_code}')

        if response.status_code == 200:
            data = response.json()
            print(f'Response structure: {list(data.keys())}')
            print(f'Number of doctors: {data.get("count", 0)}')
            print()
            print('Doctors list:')
            for i, doctor in enumerate(data.get('doctors', []), 1):
                print(f'  {i}. ID: {doctor.get("id")}')
                print(f'     Name: {doctor.get("name")}')
                print(f'     Specialization: {doctor.get("specialization")}')
                print(f'     Staff ID: {doctor.get("staff_id")}')
                print(f'     Available: {doctor.get("available")}')
                print()
        else:
            print(f'Error: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

    print('=== DOCTORS API TEST COMPLETED ===')

if __name__ == "__main__":
    test_doctors_api()
