#!/usr/bin/env python3
"""
Test Dashboard Patient Assignment Functionality
"""

import requests
import json

def test_dashboard_assignment():
    print('=== TESTING DASHBOARD PATIENT ASSIGNMENT ===')
    print()

    # Test the dashboard assignment endpoint
    print('🏥 Testing Dashboard Assignment Endpoint')
    try:
        patient_data = {
            'patient_id': 'PAT_TEST_DASH_001',
            'patient_name': 'Dashboard Test Patient',
            'age': 45,
            'gender': 'female',
            'phone': '555-0123',
            'emergency_contact': 'Emergency Contact',
            'primary_condition': 'Routine checkup',
            'severity': 'stable',
            'attending_physician': 'Dr. Smith'
        }
        
        response = requests.post('http://localhost:8000/api/beds/GEN-03/assign-new-patient',
                               json=patient_data)
        
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Success: {result.get("success", False)}')
            print(f'Patient: {result.get("patient_name")}')
            print(f'Bed: {result.get("bed_number")}')
            print(f'Patient ID: {result.get("patient_id")}')
            print(f'Message: {result.get("message")}')
        else:
            error = response.json()
            print(f'Error: {error.get("detail", "Unknown error")}')
            
    except Exception as e:
        print(f'Request Error: {e}')

    print()
    
    # Test with another bed
    print('🛏️ Testing Another Bed Assignment')
    try:
        patient_data2 = {
            'patient_id': 'PAT_TEST_DASH_002',
            'patient_name': 'Second Test Patient',
            'age': 32,
            'gender': 'male',
            'phone': '555-0456',
            'emergency_contact': 'Family Member',
            'primary_condition': 'Observation',
            'severity': 'stable',
            'attending_physician': 'Dr. Johnson'
        }
        
        response = requests.post('http://localhost:8000/api/beds/PED-02/assign-new-patient',
                               json=patient_data2)
        
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Success: {result.get("success", False)}')
            print(f'Patient: {result.get("patient_name")}')
            print(f'Bed: {result.get("bed_number")}')
        else:
            error = response.json()
            print(f'Error: {error.get("detail", "Unknown error")}')
            
    except Exception as e:
        print(f'Request Error: {e}')

    print()
    
    # Check bed status after assignments
    print('📊 Checking Bed Status After Assignments')
    try:
        response = requests.get('http://localhost:8000/api/beds')
        if response.status_code == 200:
            beds = response.json()
            occupied_beds = [bed for bed in beds if bed.get('status') == 'occupied']
            print(f'Total occupied beds: {len(occupied_beds)}')
            for bed in occupied_beds[-3:]:  # Show last 3 occupied beds
                print(f'  - {bed.get("bed_number")}: {bed.get("patient_name", "Unknown")}')
        else:
            print('Failed to get bed status')
    except Exception as e:
        print(f'Error checking beds: {e}')

    print()
    print('=== DASHBOARD ASSIGNMENT TEST COMPLETED ===')

if __name__ == "__main__":
    test_dashboard_assignment()
