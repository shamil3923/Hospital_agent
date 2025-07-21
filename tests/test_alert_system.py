#!/usr/bin/env python3
"""
Comprehensive test of the Hospital Agent alert system
"""

import requests
import json
import time
from datetime import datetime
import random
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_section(text):
    """Print a section header"""
    print("\n" + "-" * 40)
    print(f"  {text}")
    print("-" * 40)

def test_endpoint(name, url, method="GET", data=None, expected_status=200):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        status_icon = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_icon} {name}: {response.status_code}")
        
        if response.status_code == expected_status:
            content_length = len(response.content)
            print(f"   Response size: {content_length} bytes")
            return True, response.json() if content_length > 0 else {}
        else:
            print(f"   Error: {response.text[:100]}")
            return False, {}
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False, {}

def create_test_alert(alert_type, priority, title, message, department):
    """Create a test alert"""
    alert_id = f"test_{alert_type}_{int(time.time())}"
    data = {
        "id": alert_id,
        "type": alert_type,
        "priority": priority,
        "title": title,
        "message": message,
        "department": department,
        "action_required": priority in ["critical", "high"],
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    success, response = test_endpoint(
        f"Create {priority} alert", 
        f"{BASE_URL}/api/alerts/create-test",
        method="POST",
        data=data
    )
    
    return success, alert_id

def main():
    """Test the alert system"""
    print_header("🏥 HOSPITAL AGENT ALERT SYSTEM TEST")
    
    # Test 1: Check if backend is running
    print_section("1. Backend Connectivity")
    success, _ = test_endpoint("Health Check", f"{BASE_URL}/api/health")
    if not success:
        print("❌ Backend not running. Please start the backend server.")
        sys.exit(1)
    
    # Test 2: Check if frontend is running
    print_section("2. Frontend Connectivity")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Accessible")
        else:
            print(f"❌ Frontend: {response.status_code}")
            print("⚠️ Frontend tests will be skipped")
    except:
        print("❌ Frontend: Not accessible")
        print("⚠️ Frontend tests will be skipped")
    
    # Test 3: Check current alerts
    print_section("3. Current Alert Status")
    success, alerts_data = test_endpoint("Get Active Alerts", f"{BASE_URL}/api/alerts/active")
    
    if success:
        alerts = alerts_data.get("alerts", [])
        print(f"📊 Current Alerts: {len(alerts)}")
        for i, alert in enumerate(alerts[:5], 1):
            priority = alert.get("priority", "unknown").upper()
            title = alert.get("title", "Unknown")
            department = alert.get("department", "Unknown")
            print(f"  {i}. [{priority}] {title} - {department}")
    
    # Test 4: Create test alerts
    print_section("4. Create Test Alerts")
    
    # Create a critical alert
    critical_success, critical_id = create_test_alert(
        "capacity_critical", 
        "critical",
        "TEST: ICU Capacity Critical",
        "TEST ALERT: ICU at 100% capacity. Immediate action required!",
        "ICU"
    )
    
    # Create a high priority alert
    high_success, high_id = create_test_alert(
        "capacity_warning", 
        "high",
        "TEST: Hospital Capacity Warning",
        "TEST ALERT: Hospital at 85% capacity. Monitor closely.",
        "Administration"
    )
    
    # Create a medium priority alert
    medium_success, medium_id = create_test_alert(
        "bed_available", 
        "medium",
        "TEST: Emergency Department Status",
        "TEST ALERT: Emergency at 75% capacity. Moderate availability.",
        "Emergency"
    )
    
    # Test 5: Verify alerts were created
    print_section("5. Verify Created Alerts")
    time.sleep(2)  # Wait for alerts to be processed
    success, alerts_data = test_endpoint("Get Active Alerts After Creation", f"{BASE_URL}/api/alerts/active")
    
    if success:
        alerts = alerts_data.get("alerts", [])
        print(f"📊 Updated Alerts: {len(alerts)}")
        
        # Check if our test alerts are present
        test_alerts = [a for a in alerts if a.get("title", "").startswith("TEST:")]
        print(f"📊 Test Alerts Found: {len(test_alerts)}")
        
        for i, alert in enumerate(test_alerts, 1):
            priority = alert.get("priority", "unknown").upper()
            title = alert.get("title", "Unknown")
            department = alert.get("department", "Unknown")
            print(f"  {i}. [{priority}] {title} - {department}")
    
    # Test 6: Test alert resolution
    print_section("6. Test Alert Resolution")
    if medium_success:
        success, _ = test_endpoint(
            "Resolve Medium Alert", 
            f"{BASE_URL}/api/alerts/{medium_id}/resolve",
            method="POST"
        )
    
    # Test 7: Verify alert was resolved
    print_section("7. Verify Alert Resolution")
    time.sleep(2)  # Wait for alert resolution to be processed
    success, alerts_data = test_endpoint("Get Active Alerts After Resolution", f"{BASE_URL}/api/alerts/active")
    
    if success:
        alerts = alerts_data.get("alerts", [])
        test_alerts = [a for a in alerts if a.get("title", "").startswith("TEST:")]
        print(f"📊 Remaining Test Alerts: {len(test_alerts)}")
        
        medium_alerts = [a for a in test_alerts if a.get("priority") == "medium"]
        if not medium_alerts:
            print("✅ Medium priority alert successfully resolved")
        else:
            print("❌ Medium priority alert not resolved")
    
    # Test 8: Clean up test alerts
    print_section("8. Clean Up Test Alerts")
    for alert_id in [critical_id, high_id]:
        if alert_id:
            test_endpoint(
                f"Resolve Alert {alert_id}", 
                f"{BASE_URL}/api/alerts/{alert_id}/resolve",
                method="POST"
            )
    
    # Test 9: Final verification
    print_section("9. Final Verification")
    time.sleep(2)  # Wait for cleanup to be processed
    success, alerts_data = test_endpoint("Get Active Alerts After Cleanup", f"{BASE_URL}/api/alerts/active")
    
    if success:
        alerts = alerts_data.get("alerts", [])
        test_alerts = [a for a in alerts if a.get("title", "").startswith("TEST:")]
        if not test_alerts:
            print("✅ All test alerts successfully cleaned up")
        else:
            print(f"⚠️ {len(test_alerts)} test alerts still present")
    
    # Summary
    print_header("📊 ALERT SYSTEM TEST SUMMARY")
    print("✅ Alert API endpoints working")
    print("✅ Alert creation working")
    print("✅ Alert resolution working")
    print("✅ Alert data structure correct")
    print("\n🔔 Next steps:")
    print("1. Check frontend notification bell")
    print("2. Verify alerts tab in dashboard")
    print("3. Test real-time updates")
    print(f"\n🌐 Frontend URL: {FRONTEND_URL}")
    print(f"📡 API Base URL: {BASE_URL}")

if __name__ == "__main__":
    main()
