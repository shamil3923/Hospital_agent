#!/usr/bin/env python3
"""
Backend Health Check Script
"""

import requests
import json

def test_backend_health():
    print('=== BACKEND HEALTH CHECK ===')
    print()

    # Test multiple endpoints
    endpoints = [
        ('GET', '/api/beds', None),
        ('GET', '/api/alerts/active', None), 
        ('GET', '/api/beds/occupancy', None),
        ('POST', '/api/chat', {'message': 'What is the bed status?'}),
        ('GET', '/api/mcp/status', None)
    ]

    success_count = 0
    total_count = len(endpoints)

    for method, endpoint, data in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f'http://localhost:8000{endpoint}')
            else:
                response = requests.post(f'http://localhost:8000{endpoint}', json=data)
            
            if response.status_code == 200:
                print(f'✅ {method} {endpoint}: {response.status_code} OK')
                success_count += 1
                
                # Special handling for specific endpoints
                if endpoint == '/api/mcp/status':
                    result = response.json()
                    status = result.get('status', 'unknown')
                    enabled = result.get('mcp_enabled', False)
                    print(f'   MCP Status: {status}')
                    print(f'   MCP Enabled: {enabled}')
                elif endpoint == '/api/alerts/active':
                    result = response.json()
                    alerts = result.get('alerts', [])
                    print(f'   Active Alerts: {len(alerts)}')
                elif endpoint == '/api/beds/occupancy':
                    result = response.json()
                    total = result.get('total_beds', 0)
                    occupied = result.get('occupied_beds', 0)
                    print(f'   Bed Occupancy: {occupied}/{total}')
            else:
                print(f'⚠️ {method} {endpoint}: {response.status_code}')
                
        except Exception as e:
            print(f'❌ {method} {endpoint}: Error - {str(e)[:50]}...')

    print()
    print(f'=== HEALTH CHECK RESULTS ===')
    print(f'✅ Successful: {success_count}/{total_count}')
    print(f'📊 Success Rate: {success_count/total_count*100:.1f}%')
    
    if success_count == total_count:
        print('🎉 BACKEND STATUS: FULLY HEALTHY!')
    elif success_count >= total_count * 0.8:
        print('✅ BACKEND STATUS: MOSTLY HEALTHY')
    else:
        print('⚠️ BACKEND STATUS: NEEDS ATTENTION')

if __name__ == "__main__":
    test_backend_health()
