#!/usr/bin/env python3
"""
Inject persistent alerts directly into the system
"""

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def inject_alerts():
    """Inject alerts directly into the alert system"""
    try:
        # Import required modules
        from alert_system import alert_system, Alert, AlertType, AlertPriority
        from database import SessionLocal, Bed
        
        print("🏥 Injecting Persistent Alerts...")
        print("=" * 50)
        
        # Start alert system if not running
        if not alert_system.running:
            print("🚀 Starting alert system...")
            await alert_system.start_monitoring()
        
        # Get current bed data
        with SessionLocal() as db:
            # ICU data
            icu_total = db.query(Bed).filter(Bed.ward == "ICU").count()
            icu_occupied = db.query(Bed).filter(Bed.ward == "ICU", Bed.status == "occupied").count()
            icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0
            
            # Overall data
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            # Emergency data
            emergency_total = db.query(Bed).filter(Bed.ward == "Emergency").count()
            emergency_occupied = db.query(Bed).filter(Bed.ward == "Emergency", Bed.status == "occupied").count()
            emergency_rate = (emergency_occupied / emergency_total * 100) if emergency_total > 0 else 0
        
        print(f"📊 Current Status:")
        print(f"  • ICU: {icu_rate:.1f}% ({icu_occupied}/{icu_total})")
        print(f"  • Overall: {occupancy_rate:.1f}% ({occupied_beds}/{total_beds})")
        print(f"  • Emergency: {emergency_rate:.1f}% ({emergency_occupied}/{emergency_total})")
        
        # Create alerts
        alerts_created = 0
        
        # 1. ICU Critical Alert (if applicable)
        if icu_rate >= 90:
            icu_alert = Alert(
                id="",
                type=AlertType.CAPACITY_CRITICAL,
                priority=AlertPriority.CRITICAL,
                title="ICU Capacity Critical",
                message=f"ICU at {icu_rate:.1f}% capacity ({icu_occupied}/{icu_total} beds). Immediate action required!",
                department="ICU",
                action_required=True,
                metadata={
                    "icu_occupancy_rate": icu_rate,
                    "icu_total": icu_total,
                    "icu_occupied": icu_occupied,
                    "alert_type": "capacity_critical",
                    "persistent": True,
                    "recommended_actions": [
                        "Review step-down candidates",
                        "Contact overflow facilities",
                        "Expedite discharges",
                        "Activate surge protocols"
                    ]
                }
            )
            await alert_system.create_alert(icu_alert)
            print(f"🔴 Created ICU Critical Alert: {icu_alert.id}")
            alerts_created += 1
        
        # 2. General Capacity Alert
        if occupancy_rate >= 60:
            general_alert = Alert(
                id="",
                type=AlertType.CAPACITY_CRITICAL,
                priority=AlertPriority.HIGH,
                title="Hospital Capacity Alert",
                message=f"Hospital at {occupancy_rate:.1f}% capacity ({occupied_beds}/{total_beds} beds). Monitor closely.",
                department="Administration",
                action_required=True,
                metadata={
                    "occupancy_rate": occupancy_rate,
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "alert_type": "general_capacity",
                    "persistent": True
                }
            )
            await alert_system.create_alert(general_alert)
            print(f"🟠 Created General Capacity Alert: {general_alert.id}")
            alerts_created += 1
        
        # 3. Emergency Status Alert
        emergency_alert = Alert(
            id="",
            type=AlertType.BED_AVAILABLE,
            priority=AlertPriority.MEDIUM if emergency_rate < 50 else AlertPriority.HIGH,
            title="Emergency Department Status",
            message=f"Emergency department at {emergency_rate:.1f}% capacity ({emergency_occupied}/{emergency_total} beds).",
            department="Emergency",
            action_required=emergency_rate > 80,
            metadata={
                "occupancy_rate": emergency_rate,
                "total_beds": emergency_total,
                "occupied_beds": emergency_occupied,
                "alert_type": "status_update",
                "persistent": True
            }
        )
        await alert_system.create_alert(emergency_alert)
        priority_color = "🟡" if emergency_rate < 50 else "🟠"
        print(f"{priority_color} Created Emergency Status Alert: {emergency_alert.id}")
        alerts_created += 1
        
        # 4. Bed Cleaning Alert (if any beds in cleaning status)
        with SessionLocal() as db:
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
            if cleaning_beds > 0:
                cleaning_alert = Alert(
                    id="",
                    type=AlertType.CLEANING_OVERDUE,
                    priority=AlertPriority.LOW,
                    title="Bed Cleaning in Progress",
                    message=f"{cleaning_beds} beds currently in cleaning status. Monitor completion times.",
                    department="Housekeeping",
                    action_required=False,
                    metadata={
                        "cleaning_beds": cleaning_beds,
                        "alert_type": "workflow_status",
                        "persistent": True
                    }
                )
                await alert_system.create_alert(cleaning_alert)
                print(f"🔵 Created Cleaning Status Alert: {cleaning_alert.id}")
                alerts_created += 1
        
        print(f"\n✅ Created {alerts_created} persistent alerts")
        
        # Verify alerts are active
        active_alerts = alert_system.get_active_alerts()
        print(f"📊 Active alerts in system: {len(active_alerts)}")
        
        if active_alerts:
            print("\n🚨 Current Active Alerts:")
            for i, alert in enumerate(active_alerts, 1):
                priority = alert.get('priority', 'unknown').upper()
                title = alert.get('title', 'Unknown')
                department = alert.get('department', 'Unknown')
                
                priority_icon = "🔴" if priority == 'CRITICAL' else "🟠" if priority == 'HIGH' else "🟡" if priority == 'MEDIUM' else "🔵"
                print(f"  {i}. {priority_icon} [{priority}] {title} - {department}")
        
        print(f"\n🌐 Check dashboard: http://localhost:3001")
        print(f"📡 API test: curl http://localhost:8000/api/alerts/active")
        
        return len(active_alerts)
        
    except Exception as e:
        print(f"❌ Error injecting alerts: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def main():
    """Main function"""
    alert_count = await inject_alerts()
    
    if alert_count > 0:
        print(f"\n🎉 SUCCESS! {alert_count} alerts are now active in the system!")
        print("The dashboard should now show the alert count and notification bell.")
    else:
        print(f"\n❌ FAILED! No alerts are active. Check the backend logs.")

if __name__ == "__main__":
    asyncio.run(main())
