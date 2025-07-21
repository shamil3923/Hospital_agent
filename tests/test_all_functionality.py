#!/usr/bin/env python3
"""
Comprehensive test of all Hospital Agent functionalities
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            content_length = len(response.content)
            print(f"✅ {name}: {response.status_code} ({content_length} bytes)")
            return True, response.json() if content_length > 0 else {}
        else:
            print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
            return False, {}
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False, {}

def main():
    """Test all functionalities"""
    print("🏥 COMPREHENSIVE HOSPITAL AGENT FUNCTIONALITY TEST")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Basic Health Check
    print("\n📋 1. BASIC SYSTEM HEALTH")
    print("-" * 30)
    test_endpoint("Health Check", f"{base_url}/api/health")
    test_endpoint("Root Endpoint", f"{base_url}/")
    
    # Test 2: Core Data APIs
    print("\n🛏️ 2. CORE DATA APIS")
    print("-" * 30)
    success, metrics = test_endpoint("Dashboard Metrics", f"{base_url}/api/dashboard/metrics")
    success, beds = test_endpoint("Beds Data", f"{base_url}/api/beds")
    success, occupancy = test_endpoint("Bed Occupancy", f"{base_url}/api/beds/occupancy")
    success, patients = test_endpoint("Patients Data", f"{base_url}/api/patients")
    success, doctors = test_endpoint("Doctors Data", f"{base_url}/api/doctors")
    
    # Test 3: Alert System
    print("\n🚨 3. ALERT SYSTEM")
    print("-" * 30)
    success, alerts_data = test_endpoint("Active Alerts", f"{base_url}/api/alerts/active")
    test_endpoint("Create Test Alert", f"{base_url}/api/alerts/create-test", "POST")
    test_endpoint("Debug Alert System", f"{base_url}/api/debug/alert-system")
    
    if alerts_data:
        alerts = alerts_data.get("alerts", [])
        print(f"📊 Alert Details: {len(alerts)} alerts found")
        for i, alert in enumerate(alerts[:3], 1):
            priority = alert.get("priority", "unknown").upper()
            title = alert.get("title", "Unknown")
            department = alert.get("department", "Unknown")
            print(f"  {i}. [{priority}] {title} - {department}")
    
    # Test 4: Autonomous Systems
    print("\n🤖 4. AUTONOMOUS SYSTEMS")
    print("-" * 30)
    success, auto_status = test_endpoint("Autonomous Status", f"{base_url}/api/autonomous/status")
    success, predictions = test_endpoint("Autonomous Predictions", f"{base_url}/api/autonomous/predictions")
    test_endpoint("Autonomous Actions History", f"{base_url}/api/autonomous/actions/history")
    test_endpoint("System Health", f"{base_url}/api/autonomous/system-health")
    
    if auto_status:
        print("🤖 Autonomous Systems Status:")
        for system, status in auto_status.items():
            available = status.get("available", False)
            running = status.get("running", False)
            status_icon = "✅" if running else "⚠️" if available else "❌"
            print(f"  {status_icon} {system}: {'Running' if running else 'Available' if available else 'Unavailable'}")
    
    # Test 5: Predictions & Analytics
    print("\n🔮 5. PREDICTIONS & ANALYTICS")
    print("-" * 30)
    success, bed_predictions = test_endpoint("Bed Predicted Occupancy", f"{base_url}/api/beds/predicted-occupancy")
    test_endpoint("Dashboard Analytics", f"{base_url}/api/analytics/dashboard")
    test_endpoint("System Status", f"{base_url}/api/system/status")
    
    if bed_predictions:
        curve = bed_predictions.get("predicted_occupancy_curve", [])
        risk_days = bed_predictions.get("risk_days", [])
        print(f"📈 Prediction Details: {len(curve)} hours predicted, {len(risk_days)} risk periods")
    
    # Test 6: Real-time Features
    print("\n⚡ 6. REAL-TIME FEATURES")
    print("-" * 30)
    test_endpoint("Real-time Bed Status", f"{base_url}/api/beds/real-time/status")
    test_endpoint("Bed Changes", f"{base_url}/api/beds/real-time/changes")
    test_endpoint("Bed Monitoring Metrics", f"{base_url}/api/beds/real-time/metrics")
    test_endpoint("WebSocket Stats", f"{base_url}/api/websocket/stats")
    
    # Test 7: Chat Interface
    print("\n💬 7. CHAT INTERFACE")
    print("-" * 30)
    chat_success, chat_response = test_endpoint(
        "Chat API", 
        f"{base_url}/api/chat", 
        "POST", 
        {"message": "What is the current ICU occupancy?"}
    )
    
    if chat_response:
        response_text = chat_response.get("response", "")
        print(f"🤖 Chat Response Length: {len(response_text)} characters")
        print(f"🤖 Response Preview: {response_text[:100]}...")
    
    test_endpoint("Chat Performance", f"{base_url}/api/chat/performance")
    
    # Test 8: Workflow & Management
    print("\n⚙️ 8. WORKFLOW & MANAGEMENT")
    print("-" * 30)
    test_endpoint("Active Workflows", f"{base_url}/api/workflows/active")
    test_endpoint("Admission Queue", f"{base_url}/api/admissions/queue")
    test_endpoint("Clinical Recommendations", f"{base_url}/api/clinical/recommendations/active")
    
    # Test 9: Frontend Connectivity
    print("\n🌐 9. FRONTEND CONNECTIVITY")
    print("-" * 30)
    try:
        frontend_response = requests.get("http://localhost:3001", timeout=5)
        if frontend_response.status_code == 200:
            print("✅ Frontend: Accessible")
        else:
            print(f"❌ Frontend: {frontend_response.status_code}")
    except:
        print("❌ Frontend: Not accessible")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FUNCTIONALITY SUMMARY")
    print("=" * 60)
    
    if alerts_data and alerts_data.get("alerts"):
        print(f"✅ Alert System: {len(alerts_data['alerts'])} active alerts")
    else:
        print("❌ Alert System: No alerts or not working")
    
    if auto_status:
        running_systems = sum(1 for s in auto_status.values() if s.get("running", False))
        available_systems = sum(1 for s in auto_status.values() if s.get("available", False))
        print(f"🤖 Autonomous Systems: {running_systems} running, {available_systems} available")
    else:
        print("❌ Autonomous Systems: Status unavailable")
    
    if bed_predictions and bed_predictions.get("predicted_occupancy_curve"):
        print(f"🔮 Predictions: {len(bed_predictions['predicted_occupancy_curve'])} hours forecasted")
    else:
        print("❌ Predictions: Not available")
    
    if chat_response and chat_response.get("response"):
        print(f"💬 Chat Interface: Working ({len(chat_response['response'])} char response)")
    else:
        print("❌ Chat Interface: Not working")
    
    print("\n🎯 NEXT STEPS:")
    if not alerts_data or not alerts_data.get("alerts"):
        print("  • Fix alert system persistence")
    if not auto_status or not any(s.get("running") for s in auto_status.values()):
        print("  • Start autonomous systems")
    if not bed_predictions or not bed_predictions.get("predicted_occupancy_curve"):
        print("  • Enable prediction algorithms")
    
    print("\n🌐 Dashboard URL: http://localhost:3001")
    print("📡 API Base URL: http://localhost:8000")

if __name__ == "__main__":
    main()
