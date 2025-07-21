#!/usr/bin/env python3
"""
Force create alerts directly via API
"""

import requests
import json
import time
from datetime import datetime

def create_icu_alert():
    """Create ICU capacity alert via API"""
    try:
        # Create ICU alert
        alert_data = {
            "type": "capacity_critical",
            "priority": "critical",
            "title": "ICU Capacity Critical",
            "message": "ICU at 100.0% capacity (5/5 beds). Immediate action required!",
            "department": "ICU",
            "action_required": True,
            "metadata": {
                "icu_occupancy_rate": 100.0,
                "icu_total": 5,
                "icu_occupied": 5,
                "alert_type": "capacity_critical",
                "auto_generated": True,
                "recommended_actions": [
                    "Review step-down candidates",
                    "Contact overflow facilities", 
                    "Expedite discharges",
                    "Activate surge protocols"
                ]
            }
        }
        
        response = requests.post("http://localhost:8000/api/alerts/create", json=alert_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created ICU alert: {result.get('alert_id', 'unknown')}")
            return True
        else:
            print(f"❌ Failed to create ICU alert: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating ICU alert: {e}")
        return False

def create_general_alert():
    """Create general capacity alert"""
    try:
        alert_data = {
            "type": "capacity_warning",
            "priority": "high",
            "title": "Hospital Capacity Alert",
            "message": "Hospital at 61.1% capacity (11/18 beds occupied). Monitor closely.",
            "department": "Administration",
            "action_required": True,
            "metadata": {
                "occupancy_rate": 61.1,
                "total_beds": 18,
                "occupied_beds": 11,
                "alert_type": "general_capacity",
                "auto_generated": True
            }
        }
        
        response = requests.post("http://localhost:8000/api/alerts/create", json=alert_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created general alert: {result.get('alert_id', 'unknown')}")
            return True
        else:
            print(f"❌ Failed to create general alert: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating general alert: {e}")
        return False

def create_emergency_alert():
    """Create emergency department alert"""
    try:
        alert_data = {
            "type": "bed_availability",
            "priority": "medium",
            "title": "Emergency Department Status",
            "message": "Emergency department at 25% capacity (1/4 beds). Good availability.",
            "department": "Emergency",
            "action_required": False,
            "metadata": {
                "occupancy_rate": 25.0,
                "total_beds": 4,
                "occupied_beds": 1,
                "alert_type": "status_update",
                "auto_generated": True
            }
        }
        
        response = requests.post("http://localhost:8000/api/alerts/create", json=alert_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created emergency alert: {result.get('alert_id', 'unknown')}")
            return True
        else:
            print(f"❌ Failed to create emergency alert: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating emergency alert: {e}")
        return False

def check_alerts():
    """Check current active alerts"""
    try:
        response = requests.get("http://localhost:8000/api/alerts/active")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            
            print(f"\n📊 Active Alerts: {len(alerts)}")
            if alerts:
                print("-" * 60)
                for i, alert in enumerate(alerts, 1):
                    priority = alert.get('priority', 'unknown').upper()
                    title = alert.get('title', 'Unknown')
                    department = alert.get('department', 'Unknown')
                    message = alert.get('message', 'No message')
                    
                    priority_icon = "🔴" if priority == 'CRITICAL' else "🟠" if priority == 'HIGH' else "🟡" if priority == 'MEDIUM' else "🔵"
                    
                    print(f"{i:2d}. {priority_icon} [{priority}] {title}")
                    print(f"    Department: {department}")
                    print(f"    Message: {message}")
                    print()
            else:
                print("📭 No active alerts")
            
            return len(alerts)
            
        else:
            print(f"❌ Failed to get alerts: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"❌ Error checking alerts: {e}")
        return 0

def main():
    """Main function"""
    print("🏥 Force Creating Hospital Alerts")
    print("=" * 50)
    
    # Check current alerts
    current_count = check_alerts()
    
    if current_count == 0:
        print("\n🚨 No alerts found. Creating alerts...")
        
        # Create alerts
        success_count = 0
        
        if create_icu_alert():
            success_count += 1
            time.sleep(1)
        
        if create_general_alert():
            success_count += 1
            time.sleep(1)
            
        if create_emergency_alert():
            success_count += 1
            time.sleep(1)
        
        print(f"\n✅ Created {success_count}/3 alerts")
        
        # Check alerts again
        print("\n📊 Updated Alert Status:")
        final_count = check_alerts()
        
        if final_count > 0:
            print(f"\n🎉 Success! Dashboard should now show {final_count} active alerts")
            print("🌐 Check dashboard: http://localhost:3001")
        else:
            print("\n❌ No alerts created. Check backend logs for errors.")
    
    else:
        print(f"\n✅ {current_count} alerts already active")
        print("🌐 Check dashboard: http://localhost:3001")

if __name__ == "__main__":
    main()
