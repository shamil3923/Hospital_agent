"""
Enhanced data initialization with comprehensive hospital data
"""
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Department, Staff, Equipment
import random

def create_enhanced_sample_data():
    """Create comprehensive sample data for the hospital system"""
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(AgentLog).delete()
        db.query(BedOccupancyHistory).delete()
        db.query(Equipment).delete()
        db.query(Staff).delete()
        db.query(Patient).delete()
        db.query(Bed).delete()
        db.query(Department).delete()
        
        # Create Departments
        departments = [
            Department(
                name="ICU",
                description="Intensive Care Unit - Critical care for life-threatening conditions",
                floor_number=3,
                wing="North",
                head_of_department="Dr. Sarah Johnson",
                contact_extension="3001",
                total_beds=20,
                available_beds=3,
                specialization="Critical Care",
                equipment_available=json.dumps(["ventilators", "cardiac_monitors", "defibrillators", "infusion_pumps"]),
                operating_hours="24/7",
                emergency_contact="3001",
                budget_allocated=2500000.0
            ),
            Department(
                name="Emergency",
                description="Emergency Department - Immediate care for urgent medical conditions",
                floor_number=1,
                wing="East",
                head_of_department="Dr. Michael Chen",
                contact_extension="2001",
                total_beds=25,
                available_beds=5,
                specialization="Emergency Medicine",
                equipment_available=json.dumps(["trauma_carts", "x_ray", "ultrasound", "cardiac_monitors"]),
                operating_hours="24/7",
                emergency_contact="2001",
                budget_allocated=1800000.0
            ),
            Department(
                name="General",
                description="General Medical Ward - Standard inpatient care",
                floor_number=2,
                wing="South",
                head_of_department="Dr. Emily Rodriguez",
                contact_extension="2501",
                total_beds=40,
                available_beds=8,
                specialization="Internal Medicine",
                equipment_available=json.dumps(["basic_monitors", "iv_pumps", "oxygen"]),
                operating_hours="24/7",
                emergency_contact="2501",
                budget_allocated=1200000.0
            ),
            Department(
                name="Pediatric",
                description="Pediatric Ward - Specialized care for children",
                floor_number=4,
                wing="West",
                head_of_department="Dr. Lisa Park",
                contact_extension="4001",
                total_beds=15,
                available_beds=3,
                specialization="Pediatrics",
                equipment_available=json.dumps(["pediatric_monitors", "incubators", "specialized_beds"]),
                operating_hours="24/7",
                emergency_contact="4001",
                budget_allocated=900000.0
            ),
            Department(
                name="Maternity",
                description="Maternity Ward - Obstetric and newborn care",
                floor_number=5,
                wing="North",
                head_of_department="Dr. Amanda Wilson",
                contact_extension="5001",
                total_beds=12,
                available_beds=2,
                specialization="Obstetrics",
                equipment_available=json.dumps(["fetal_monitors", "delivery_beds", "nicu_equipment"]),
                operating_hours="24/7",
                emergency_contact="5001",
                budget_allocated=800000.0
            )
        ]
        
        for dept in departments:
            db.add(dept)
        db.commit()
        
        # Create Staff
        staff_members = [
            # ICU Staff
            Staff(staff_id="DOC001", name="Dr. Sarah Johnson", role="doctor", department_id=1, 
                  specialization="Critical Care", phone="555-3001", email="s.johnson@hospital.com",
                  shift_schedule="day", hire_date=datetime(2020, 1, 15), license_number="MD123456"),
            Staff(staff_id="NUR001", name="Jennifer Adams", role="nurse", department_id=1,
                  specialization="ICU", phone="555-3002", email="j.adams@hospital.com",
                  shift_schedule="day", hire_date=datetime(2021, 3, 10), license_number="RN789012"),
            Staff(staff_id="NUR002", name="Robert Kim", role="nurse", department_id=1,
                  specialization="ICU", phone="555-3003", email="r.kim@hospital.com",
                  shift_schedule="night", hire_date=datetime(2019, 8, 22), license_number="RN345678"),
            
            # Emergency Staff
            Staff(staff_id="DOC002", name="Dr. Michael Chen", role="doctor", department_id=2,
                  specialization="Emergency Medicine", phone="555-2001", email="m.chen@hospital.com",
                  shift_schedule="rotating", hire_date=datetime(2018, 5, 20), license_number="MD234567"),
            Staff(staff_id="NUR003", name="Maria Gonzalez", role="nurse", department_id=2,
                  specialization="Emergency", phone="555-2002", email="m.gonzalez@hospital.com",
                  shift_schedule="day", hire_date=datetime(2020, 11, 5), license_number="RN456789"),
            
            # General Ward Staff
            Staff(staff_id="DOC003", name="Dr. Emily Rodriguez", role="doctor", department_id=3,
                  specialization="Internal Medicine", phone="555-2501", email="e.rodriguez@hospital.com",
                  shift_schedule="day", hire_date=datetime(2017, 9, 12), license_number="MD345678"),
            Staff(staff_id="NUR004", name="David Thompson", role="nurse", department_id=3,
                  specialization="Medical-Surgical", phone="555-2502", email="d.thompson@hospital.com",
                  shift_schedule="day", hire_date=datetime(2022, 1, 8), license_number="RN567890"),
            
            # Support Staff
            Staff(staff_id="TEC001", name="James Wilson", role="technician", department_id=1,
                  specialization="Biomedical", phone="555-1001", email="j.wilson@hospital.com",
                  shift_schedule="day", hire_date=datetime(2019, 4, 15), license_number="BMT12345"),
            Staff(staff_id="ADM001", name="Susan Lee", role="admin", department_id=3,
                  specialization="Bed Management", phone="555-1002", email="s.lee@hospital.com",
                  shift_schedule="day", hire_date=datetime(2021, 7, 20), license_number="ADM67890")
        ]
        
        for staff in staff_members:
            db.add(staff)
        db.commit()
        
        print("✅ Created departments and staff")
        
        # Create Enhanced Beds
        beds_data = []
        bed_id = 1
        
        # ICU Beds (20 beds)
        for i in range(1, 21):
            beds_data.append({
                "bed_number": f"ICU-{i:02d}",
                "room_number": f"301{i:02d}",
                "ward": "ICU",
                "bed_type": "ICU",
                "floor_number": 3,
                "wing": "North",
                "equipment": json.dumps(["ventilator", "cardiac_monitor", "infusion_pump_1", "infusion_pump_2", "defibrillator"]),
                "isolation_required": i <= 3,  # First 3 are isolation rooms
                "private_room": True,
                "daily_rate": 2500.0
            })
        
        # Emergency Beds (25 beds)
        for i in range(1, 26):
            beds_data.append({
                "bed_number": f"ER-{i:02d}",
                "room_number": f"101{i:02d}",
                "ward": "Emergency",
                "bed_type": "Emergency",
                "floor_number": 1,
                "wing": "East",
                "equipment": json.dumps(["cardiac_monitor", "oxygen", "suction"]),
                "isolation_required": False,
                "private_room": i <= 5,  # First 5 are private
                "daily_rate": 1200.0
            })
        
        # General Beds (40 beds)
        for i in range(1, 41):
            beds_data.append({
                "bed_number": f"GEN-{i:02d}",
                "room_number": f"201{i:02d}",
                "ward": "General",
                "bed_type": "General",
                "floor_number": 2,
                "wing": "South",
                "equipment": json.dumps(["basic_monitor", "oxygen"]),
                "isolation_required": False,
                "private_room": i <= 10,  # First 10 are private
                "daily_rate": 800.0
            })
        
        # Pediatric Beds (15 beds)
        for i in range(1, 16):
            beds_data.append({
                "bed_number": f"PED-{i:02d}",
                "room_number": f"401{i:02d}",
                "ward": "Pediatric",
                "bed_type": "Pediatric",
                "floor_number": 4,
                "wing": "West",
                "equipment": json.dumps(["pediatric_monitor", "oxygen", "specialized_bed"]),
                "isolation_required": i <= 2,
                "private_room": True,
                "daily_rate": 1000.0
            })
        
        # Maternity Beds (12 beds)
        for i in range(1, 13):
            beds_data.append({
                "bed_number": f"MAT-{i:02d}",
                "room_number": f"501{i:02d}",
                "ward": "Maternity",
                "bed_type": "Maternity",
                "floor_number": 5,
                "wing": "North",
                "equipment": json.dumps(["fetal_monitor", "delivery_bed", "oxygen"]),
                "isolation_required": False,
                "private_room": True,
                "daily_rate": 1500.0
            })
        
        # Create bed objects
        beds = []
        for bed_data in beds_data:
            # Randomly assign status
            status_options = ["occupied", "vacant", "cleaning", "maintenance"]
            weights = [0.75, 0.15, 0.08, 0.02]  # 75% occupied, 15% vacant, etc.
            status = random.choices(status_options, weights=weights)[0]
            
            bed = Bed(
                bed_number=bed_data["bed_number"],
                room_number=bed_data["room_number"],
                ward=bed_data["ward"],
                bed_type=bed_data["bed_type"],
                status=status,
                floor_number=bed_data["floor_number"],
                wing=bed_data["wing"],
                equipment=bed_data["equipment"],
                isolation_required=bed_data["isolation_required"],
                private_room=bed_data["private_room"],
                daily_rate=bed_data["daily_rate"],
                last_cleaned=datetime.now() - timedelta(hours=random.randint(1, 24)),
                last_updated=datetime.now()
            )
            beds.append(bed)
        
        for bed in beds:
            db.add(bed)
        db.commit()
        
        print(f"✅ Created {len(beds)} beds")
        
        # Get bed IDs for patient assignment
        bed_ids = [bed.id for bed in db.query(Bed).filter(Bed.status == "occupied").all()]
        
        print(f"✅ Enhanced hospital data created successfully!")
        print(f"📊 Summary:")
        print(f"   - Departments: {len(departments)}")
        print(f"   - Staff: {len(staff_members)}")
        print(f"   - Beds: {len(beds)}")
        print(f"   - Occupied beds: {len(bed_ids)}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_enhanced_sample_data()
