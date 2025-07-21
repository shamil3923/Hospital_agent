#!/usr/bin/env python3
"""
Manage alerts for the Hospital Agent dashboard
"""

import requests
import json
import sys
from datetime import datetime

def get_active_alerts():
    """Get current active alerts"""
    try:
        response = requests.get("http://localhost:8000/api/alerts/active")
        if response.status_code == 200:
            data = response.json()
            return data.get("alerts", [])
        else:
            print(f"❌ HTTP Error getting alerts: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")
        return []

def resolve_alert(alert_id):
    """Resolve a specific alert"""
    try:
        response = requests.post(f"http://localhost:8000/api/alerts/{alert_id}/resolve")
        if response.status_code == 200:
            print(f"✅ Resolved alert: {alert_id}")
            return True
        else:
            print(f"❌ Failed to resolve alert {alert_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error resolving alert {alert_id}: {e}")
        return False

def create_test_alert():
    """Create a test alert"""
    try:
        response = requests.post("http://localhost:8000/api/alerts/create-test")
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Created alert: {result.get('alert_id')}")
                return True
            else:
                print(f"❌ Failed to create alert: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating alert: {e}")
        return False

def display_alerts():
    """Display current alerts"""
    alerts = get_active_alerts()
    
    if not alerts:
        print("📭 No active alerts")
        return
    
    print(f"📊 Active Alerts ({len(alerts)}):")
    print("-" * 80)
    
    for i, alert in enumerate(alerts, 1):
        priority = alert.get('priority', 'unknown').upper()
        title = alert.get('title', 'Unknown')
        department = alert.get('department', 'Unknown')
        message = alert.get('message', 'No message')
        created_time = alert.get('created_at', '')
        alert_id = alert.get('id', 'unknown')
        
        # Parse time for display
        try:
            if created_time:
                dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            else:
                time_str = 'Unknown'
        except:
            time_str = 'Unknown'
        
        print(f"{i:2d}. [{priority}] {title}")
        print(f"    Department: {department} | Time: {time_str}")
        print(f"    Message: {message}")
        print(f"    ID: {alert_id}")
        print()

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🏥 Hospital Alert Management Tool")
        print("\nUsage:")
        print("  python manage_alerts.py list          - Show all active alerts")
        print("  python manage_alerts.py create        - Create a test alert")
        print("  python manage_alerts.py resolve <id>  - Resolve specific alert")
        print("  python manage_alerts.py clear         - Resolve all alerts")
        print("\nExamples:")
        print("  python manage_alerts.py list")
        print("  python manage_alerts.py create")
        print("  python manage_alerts.py resolve capacity_critical_Dashboard_123456")
        print("  python manage_alerts.py clear")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        display_alerts()
        
    elif command == "create":
        print("🚨 Creating test alert...")
        if create_test_alert():
            print("\n📊 Updated alert list:")
            display_alerts()
        
    elif command == "resolve":
        if len(sys.argv) < 3:
            print("❌ Please provide alert ID to resolve")
            print("Usage: python manage_alerts.py resolve <alert_id>")
            return
        
        alert_id = sys.argv[2]
        print(f"🔧 Resolving alert: {alert_id}")
        if resolve_alert(alert_id):
            print("\n📊 Updated alert list:")
            display_alerts()
        
    elif command == "clear":
        print("🧹 Clearing all active alerts...")
        alerts = get_active_alerts()
        if not alerts:
            print("📭 No alerts to clear")
            return
        
        resolved_count = 0
        for alert in alerts:
            alert_id = alert.get('id')
            if alert_id and resolve_alert(alert_id):
                resolved_count += 1
        
        print(f"\n✅ Resolved {resolved_count}/{len(alerts)} alerts")
        
        # Show remaining alerts
        remaining = get_active_alerts()
        if remaining:
            print(f"\n⚠️ {len(remaining)} alerts could not be resolved:")
            display_alerts()
        else:
            print("🎉 All alerts cleared successfully!")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, create, resolve, clear")

if __name__ == "__main__":
    main()
