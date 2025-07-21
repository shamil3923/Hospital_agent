#!/usr/bin/env python3
"""
Trigger ICU capacity alert for testing
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def trigger_icu_alert():
    """Force trigger ICU capacity alert"""
    try:
        from alert_system import alert_system
        
        print("🏥 Checking ICU capacity and triggering alerts...")
        
        # Start alert system if not running
        if not alert_system.running:
            print("🚀 Starting alert system...")
            await alert_system.start_monitoring()
        
        # Force capacity monitoring
        print("🔍 Checking capacity levels...")
        await alert_system._monitor_capacity_levels()
        
        # Get active alerts
        alerts = alert_system.get_active_alerts()
        
        print(f"\n📊 Active Alerts: {len(alerts)}")
        
        icu_alerts = [a for a in alerts if a.get('department') == 'ICU']
        if icu_alerts:
            print("🚨 ICU Alerts Found:")
            for alert in icu_alerts:
                priority = alert.get('priority', 'unknown').upper()
                title = alert.get('title', 'Unknown')
                message = alert.get('message', 'No message')
                print(f"  • [{priority}] {title}")
                print(f"    {message}")
        else:
            print("⚠️ No ICU alerts found")
        
        print(f"\n🌐 Check dashboard: http://localhost:3001")
        print(f"📡 API endpoint: http://localhost:8000/api/alerts/active")
        
        return len(alerts)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    alert_count = asyncio.run(trigger_icu_alert())
    print(f"\n✅ Triggered {alert_count} total alerts")
