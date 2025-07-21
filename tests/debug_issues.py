#!/usr/bin/env python3
"""
Debug Current Issues
"""

import requests
import json

def check_doctors_api():
    print('=== CHECKING DOCTORS API ===')
    try:
        response = requests.get('http://localhost:8000/api/doctors')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Response keys: {list(data.keys())}')
            print(f'Doctors count: {data.get("count", 0)}')
            print(f'Doctors array length: {len(data.get("doctors", []))}')
            
            print('\nDoctors list:')
            for i, doctor in enumerate(data.get('doctors', []), 1):
                print(f'{i}. {doctor}')
        else:
            print(f'Error response: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

def check_alerts_api():
    print('\n=== CHECKING ALERTS API ===')
    try:
        response = requests.get('http://localhost:8000/api/alerts/active')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f'Active alerts count: {len(alerts)}')
            
            for i, alert in enumerate(alerts, 1):
                print(f'{i}. [{alert.get("priority", "unknown").upper()}] {alert.get("title", "No title")}')
                print(f'   Message: {alert.get("message", "No message")}')
                print(f'   Department: {alert.get("department", "Unknown")}')
        else:
            print(f'Error response: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

def check_bed_occupancy():
    print('\n=== CHECKING BED OCCUPANCY ===')
    try:
        response = requests.get('http://localhost:8000/api/beds/occupancy')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Total beds: {data.get("total_beds", 0)}')
            print(f'Occupied beds: {data.get("occupied_beds", 0)}')
            print(f'Overall occupancy: {data.get("occupancy_rate", 0)}%')
            
            ward_breakdown = data.get('ward_breakdown', {})
            print('\nWard breakdown:')
            for ward, stats in ward_breakdown.items():
                occupancy = (stats['occupied'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f'  {ward}: {occupancy:.1f}% ({stats["occupied"]}/{stats["total"]})')
                
                if occupancy >= 90:
                    print(f'    ⚠️ CRITICAL: {ward} at {occupancy:.1f}% - Should trigger alert!')
                    
        else:
            print(f'Error response: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

if __name__ == "__main__":
    check_doctors_api()
    check_alerts_api()
    check_bed_occupancy()
