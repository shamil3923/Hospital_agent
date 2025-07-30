"""
Comprehensive Hospital Database Enrichment Script
Creates realistic data for a 500-bed hospital with multiple departments
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import json

from backend.database import SessionLocal, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog, Staff, Department, Equipment

# Realistic hospital data
DEPARTMENTS = [
    {"name": "ICU", "description": "Intensive Care Unit", "floor_number": 3, "wing": "North", "total_beds": 40, "specialization": "Critical Care"},
    {"name": "Emergency", "description": "Emergency Department", "floor_number": 1, "wing": "East", "total_beds": 25, "specialization": "Emergency Medicine"},
    {"name": "Cardiology", "description": "Cardiac Care Unit", "floor_number": 4, "wing": "South", "total_beds": 35, "specialization": "Cardiology"},
    {"name": "Neurology", "description": "Neurological Care", "floor_number": 5, "wing": "West", "total_beds": 30, "specialization": "Neurology"},
    {"name": "Orthopedics", "description": "Orthopedic Surgery", "floor_number": 2, "wing": "North", "total_beds": 45, "specialization": "Orthopedic Surgery"},
    {"name": "Pediatrics", "description": "Children's Ward", "floor_number": 6, "wing": "East", "total_beds": 40, "specialization": "Pediatrics"},
    {"name": "Maternity", "description": "Maternity Ward", "floor_number": 7, "wing": "South", "total_beds": 35, "specialization": "Obstetrics"},
    {"name": "General Medicine", "description": "General Medical Ward", "floor_number": 2, "wing": "South", "total_beds": 60, "specialization": "Internal Medicine"},
    {"name": "Surgery", "description": "Surgical Ward", "floor_number": 3, "wing": "West", "total_beds": 50, "specialization": "General Surgery"},
    {"name": "Oncology", "description": "Cancer Treatment Center", "floor_number": 8, "wing": "North", "total_beds": 30, "specialization": "Oncology"},
    {"name": "Psychiatry", "description": "Mental Health Unit", "floor_number": 9, "wing": "West", "total_beds": 25, "specialization": "Psychiatry"},
    {"name": "Rehabilitation", "description": "Physical Rehabilitation", "floor_number": 1, "wing": "West", "total_beds": 35, "specialization": "Physical Medicine"}
]

STAFF_DATA = [
    # ICU Staff
    {"staff_id": "DOC001", "name": "Dr. Sarah Johnson", "role": "doctor", "specialization": "Critical Care Medicine", "department": "ICU"},
    {"staff_id": "DOC002", "name": "Dr. Michael Chen", "role": "doctor", "specialization": "Pulmonology", "department": "ICU"},
    {"staff_id": "DOC003", "name": "Dr. Emily Rodriguez", "role": "doctor", "specialization": "Cardiothoracic Surgery", "department": "ICU"},
    {"staff_id": "DOC004", "name": "Dr. James Wilson", "role": "doctor", "specialization": "Anesthesiology", "department": "ICU"},
    
    # Emergency Staff
    {"staff_id": "DOC005", "name": "Dr. Lisa Thompson", "role": "doctor", "specialization": "Emergency Medicine", "department": "Emergency"},
    {"staff_id": "DOC006", "name": "Dr. Robert Davis", "role": "doctor", "specialization": "Trauma Surgery", "department": "Emergency"},
    {"staff_id": "DOC007", "name": "Dr. Amanda White", "role": "doctor", "specialization": "Emergency Medicine", "department": "Emergency"},
    {"staff_id": "DOC008", "name": "Dr. Kevin Brown", "role": "doctor", "specialization": "Emergency Pediatrics", "department": "Emergency"},
    
    # Cardiology Staff
    {"staff_id": "DOC009", "name": "Dr. Maria Garcia", "role": "doctor", "specialization": "Interventional Cardiology", "department": "Cardiology"},
    {"staff_id": "DOC010", "name": "Dr. David Miller", "role": "doctor", "specialization": "Electrophysiology", "department": "Cardiology"},
    {"staff_id": "DOC011", "name": "Dr. Jennifer Lee", "role": "doctor", "specialization": "Heart Failure", "department": "Cardiology"},
    {"staff_id": "DOC012", "name": "Dr. Thomas Anderson", "role": "doctor", "specialization": "Cardiac Surgery", "department": "Cardiology"},
    
    # Neurology Staff
    {"staff_id": "DOC013", "name": "Dr. Rachel Green", "role": "doctor", "specialization": "Stroke Medicine", "department": "Neurology"},
    {"staff_id": "DOC014", "name": "Dr. Christopher Taylor", "role": "doctor", "specialization": "Neurosurgery", "department": "Neurology"},
    {"staff_id": "DOC015", "name": "Dr. Nicole Martinez", "role": "doctor", "specialization": "Epilepsy", "department": "Neurology"},
    {"staff_id": "DOC016", "name": "Dr. Steven Clark", "role": "doctor", "specialization": "Movement Disorders", "department": "Neurology"},
    
    # Orthopedics Staff
    {"staff_id": "DOC017", "name": "Dr. Patricia Lewis", "role": "doctor", "specialization": "Joint Replacement", "department": "Orthopedics"},
    {"staff_id": "DOC018", "name": "Dr. Mark Robinson", "role": "doctor", "specialization": "Sports Medicine", "department": "Orthopedics"},
    {"staff_id": "DOC019", "name": "Dr. Laura Walker", "role": "doctor", "specialization": "Spine Surgery", "department": "Orthopedics"},
    {"staff_id": "DOC020", "name": "Dr. Daniel Hall", "role": "doctor", "specialization": "Trauma Orthopedics", "department": "Orthopedics"},
    
    # Pediatrics Staff
    {"staff_id": "DOC021", "name": "Dr. Susan Young", "role": "doctor", "specialization": "Pediatric Cardiology", "department": "Pediatrics"},
    {"staff_id": "DOC022", "name": "Dr. Brian King", "role": "doctor", "specialization": "Pediatric Surgery", "department": "Pediatrics"},
    {"staff_id": "DOC023", "name": "Dr. Michelle Wright", "role": "doctor", "specialization": "Neonatology", "department": "Pediatrics"},
    {"staff_id": "DOC024", "name": "Dr. Andrew Lopez", "role": "doctor", "specialization": "Pediatric Oncology", "department": "Pediatrics"},
    
    # Maternity Staff
    {"staff_id": "DOC025", "name": "Dr. Karen Hill", "role": "doctor", "specialization": "Obstetrics", "department": "Maternity"},
    {"staff_id": "DOC026", "name": "Dr. Joseph Scott", "role": "doctor", "specialization": "Maternal-Fetal Medicine", "department": "Maternity"},
    {"staff_id": "DOC027", "name": "Dr. Elizabeth Adams", "role": "doctor", "specialization": "Gynecology", "department": "Maternity"},
    {"staff_id": "DOC028", "name": "Dr. Richard Baker", "role": "doctor", "specialization": "Reproductive Endocrinology", "department": "Maternity"},
    
    # General Medicine Staff
    {"staff_id": "DOC029", "name": "Dr. Nancy Gonzalez", "role": "doctor", "specialization": "Internal Medicine", "department": "General Medicine"},
    {"staff_id": "DOC030", "name": "Dr. William Nelson", "role": "doctor", "specialization": "Geriatrics", "department": "General Medicine"},
    {"staff_id": "DOC031", "name": "Dr. Donna Carter", "role": "doctor", "specialization": "Infectious Disease", "department": "General Medicine"},
    {"staff_id": "DOC032", "name": "Dr. Paul Mitchell", "role": "doctor", "specialization": "Endocrinology", "department": "General Medicine"},
    
    # Surgery Staff
    {"staff_id": "DOC033", "name": "Dr. Carol Perez", "role": "doctor", "specialization": "General Surgery", "department": "Surgery"},
    {"staff_id": "DOC034", "name": "Dr. Gary Roberts", "role": "doctor", "specialization": "Vascular Surgery", "department": "Surgery"},
    {"staff_id": "DOC035", "name": "Dr. Helen Turner", "role": "doctor", "specialization": "Plastic Surgery", "department": "Surgery"},
    {"staff_id": "DOC036", "name": "Dr. Frank Phillips", "role": "doctor", "specialization": "Urological Surgery", "department": "Surgery"},
    
    # Oncology Staff
    {"staff_id": "DOC037", "name": "Dr. Betty Campbell", "role": "doctor", "specialization": "Medical Oncology", "department": "Oncology"},
    {"staff_id": "DOC038", "name": "Dr. Ronald Parker", "role": "doctor", "specialization": "Radiation Oncology", "department": "Oncology"},
    {"staff_id": "DOC039", "name": "Dr. Dorothy Evans", "role": "doctor", "specialization": "Surgical Oncology", "department": "Oncology"},
    {"staff_id": "DOC040", "name": "Dr. Kenneth Edwards", "role": "doctor", "specialization": "Hematology", "department": "Oncology"},
    
    # Psychiatry Staff
    {"staff_id": "DOC041", "name": "Dr. Sandra Collins", "role": "doctor", "specialization": "Adult Psychiatry", "department": "Psychiatry"},
    {"staff_id": "DOC042", "name": "Dr. Larry Stewart", "role": "doctor", "specialization": "Child Psychiatry", "department": "Psychiatry"},
    {"staff_id": "DOC043", "name": "Dr. Kimberly Morris", "role": "doctor", "specialization": "Addiction Medicine", "department": "Psychiatry"},
    {"staff_id": "DOC044", "name": "Dr. Anthony Reed", "role": "doctor", "specialization": "Geriatric Psychiatry", "department": "Psychiatry"},
    
    # Rehabilitation Staff
    {"staff_id": "DOC045", "name": "Dr. Lisa Cook", "role": "doctor", "specialization": "Physical Medicine", "department": "Rehabilitation"},
    {"staff_id": "DOC046", "name": "Dr. Charles Morgan", "role": "doctor", "specialization": "Occupational Medicine", "department": "Rehabilitation"},
    {"staff_id": "DOC047", "name": "Dr. Deborah Bell", "role": "doctor", "specialization": "Sports Rehabilitation", "department": "Rehabilitation"},
    {"staff_id": "DOC048", "name": "Dr. Jason Murphy", "role": "doctor", "specialization": "Neurological Rehabilitation", "department": "Rehabilitation"}
]

MEDICAL_CONDITIONS = [
    # Critical conditions
    {"condition": "Myocardial Infarction", "severity": "critical", "typical_ward": "ICU", "avg_stay_days": 7},
    {"condition": "Stroke", "severity": "critical", "typical_ward": "Neurology", "avg_stay_days": 10},
    {"condition": "Sepsis", "severity": "critical", "typical_ward": "ICU", "avg_stay_days": 14},
    {"condition": "Respiratory Failure", "severity": "critical", "typical_ward": "ICU", "avg_stay_days": 12},
    {"condition": "Cardiac Arrest", "severity": "critical", "typical_ward": "ICU", "avg_stay_days": 8},
    
    # Serious conditions
    {"condition": "Pneumonia", "severity": "serious", "typical_ward": "General Medicine", "avg_stay_days": 5},
    {"condition": "Heart Failure", "severity": "serious", "typical_ward": "Cardiology", "avg_stay_days": 6},
    {"condition": "Diabetic Ketoacidosis", "severity": "serious", "typical_ward": "General Medicine", "avg_stay_days": 4},
    {"condition": "Pulmonary Embolism", "severity": "serious", "typical_ward": "General Medicine", "avg_stay_days": 7},
    {"condition": "Acute Pancreatitis", "severity": "serious", "typical_ward": "General Medicine", "avg_stay_days": 8},
    
    # Stable conditions
    {"condition": "Hip Replacement", "severity": "stable", "typical_ward": "Orthopedics", "avg_stay_days": 3},
    {"condition": "Appendectomy", "severity": "stable", "typical_ward": "Surgery", "avg_stay_days": 2},
    {"condition": "Cholecystectomy", "severity": "stable", "typical_ward": "Surgery", "avg_stay_days": 1},
    {"condition": "Hernia Repair", "severity": "stable", "typical_ward": "Surgery", "avg_stay_days": 1},
    {"condition": "Cataract Surgery", "severity": "stable", "typical_ward": "Surgery", "avg_stay_days": 1}
]

def clear_existing_data(db: Session):
    """Clear existing data to start fresh"""
    print("🗑️ Clearing existing data...")
    
    # Delete in reverse order of dependencies
    db.query(BedOccupancyHistory).delete()
    db.query(AgentLog).delete()
    db.query(Equipment).delete()
    db.query(Patient).delete()
    db.query(Bed).delete()
    db.query(Staff).delete()
    db.query(Department).delete()
    
    db.commit()
    print("✅ Existing data cleared")

def create_departments(db: Session):
    """Create hospital departments"""
    print("🏢 Creating hospital departments...")
    
    for dept_data in DEPARTMENTS:
        dept = Department(
            name=dept_data["name"],
            description=dept_data["description"],
            floor_number=dept_data["floor_number"],
            wing=dept_data["wing"],
            total_beds=dept_data["total_beds"],
            available_beds=dept_data["total_beds"],  # Initially all available
            specialization=dept_data["specialization"],
            operating_hours="24/7" if dept_data["name"] in ["ICU", "Emergency"] else "06:00-22:00",
            head_of_department=f"Dr. {dept_data['name']} Chief",
            contact_extension=f"ext-{random.randint(1000, 9999)}"
        )
        db.add(dept)
    
    db.commit()
    print(f"✅ Created {len(DEPARTMENTS)} departments")

def create_comprehensive_staff(db: Session):
    """Create comprehensive hospital staff"""
    print("👨‍⚕️ Creating hospital staff...")
    
    departments = {dept.name: dept.id for dept in db.query(Department).all()}
    
    for staff_data in STAFF_DATA:
        dept_id = departments.get(staff_data["department"])
        
        staff = Staff(
            staff_id=staff_data["staff_id"],
            name=staff_data["name"],
            role=staff_data["role"],
            department_id=dept_id,
            specialization=staff_data["specialization"],
            phone=f"555-{random.randint(1000, 9999)}",
            email=f"{staff_data['name'].lower().replace(' ', '.')}@hospital.com",
            shift_schedule=random.choice(["day", "night", "rotating"]),
            hire_date=datetime.now() - timedelta(days=random.randint(30, 3650)),
            license_number=f"LIC{random.randint(100000, 999999)}",
            status="active"
        )
        db.add(staff)
    
    # Add nurses (3 nurses per doctor)
    nurse_counter = 1
    for staff_data in STAFF_DATA:
        dept_id = departments.get(staff_data["department"])
        
        for i in range(3):
            nurse = Staff(
                staff_id=f"NUR{nurse_counter:03d}",
                name=f"Nurse {['Alice', 'Bob', 'Carol', 'David', 'Emma', 'Frank', 'Grace', 'Henry'][i % 8]} {['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'][i % 5]}",
                role="nurse",
                department_id=dept_id,
                specialization=staff_data["specialization"],
                phone=f"555-{random.randint(1000, 9999)}",
                email=f"nurse{nurse_counter}@hospital.com",
                shift_schedule=random.choice(["day", "night", "rotating"]),
                hire_date=datetime.now() - timedelta(days=random.randint(30, 2000)),
                license_number=f"RN{random.randint(100000, 999999)}",
                status="active"
            )
            db.add(nurse)
            nurse_counter += 1
    
    db.commit()
    print(f"✅ Created {len(STAFF_DATA)} doctors and {len(STAFF_DATA) * 3} nurses")

def create_comprehensive_beds(db: Session):
    """Create comprehensive bed inventory"""
    print("🛏️ Creating hospital beds...")

    departments = db.query(Department).all()
    bed_counter = 1

    for dept in departments:
        for bed_num in range(1, dept.total_beds + 1):
            # Determine bed type based on department
            if dept.name == "ICU":
                bed_type = "ICU"
                equipment = json.dumps(["ventilator", "cardiac_monitor", "infusion_pump", "defibrillator"])
                private_room = True
            elif dept.name == "Emergency":
                bed_type = "Emergency"
                equipment = json.dumps(["cardiac_monitor", "oxygen", "trauma_kit"])
                private_room = False
            elif dept.name == "Maternity":
                bed_type = "Maternity"
                equipment = json.dumps(["fetal_monitor", "birthing_bed", "infant_warmer"])
                private_room = True
            elif dept.name == "Pediatrics":
                bed_type = "Pediatric"
                equipment = json.dumps(["pediatric_monitor", "oxygen", "toys"])
                private_room = False
            else:
                bed_type = "General"
                equipment = json.dumps(["basic_monitor", "oxygen"])
                private_room = random.choice([True, False])

            # Realistic bed status distribution
            status_weights = {
                "occupied": 0.75,  # 75% occupancy rate
                "vacant": 0.20,    # 20% vacant
                "cleaning": 0.03,  # 3% cleaning
                "maintenance": 0.02 # 2% maintenance
            }
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]

            bed = Bed(
                bed_number=f"{dept.name[:3].upper()}-{bed_num:03d}",
                room_number=f"{dept.floor_number}{bed_num:02d}",
                ward=dept.name,
                bed_type=bed_type,
                status=status,
                floor_number=dept.floor_number,
                wing=dept.wing,
                equipment=equipment,
                isolation_required=random.choice([True, False]) if dept.name in ["ICU", "General Medicine"] else False,
                private_room=private_room,
                last_cleaned=datetime.now() - timedelta(hours=random.randint(1, 24)),
                maintenance_notes=f"Bed in {dept.name} department"
            )

            if status == "occupied":
                bed.admission_time = datetime.now() - timedelta(hours=random.randint(1, 168))
                bed.expected_discharge = datetime.now() + timedelta(hours=random.randint(12, 240))

            db.add(bed)
            bed_counter += 1

    db.commit()
    print(f"✅ Created {bed_counter - 1} beds across all departments")

def create_realistic_patients(db: Session):
    """Create realistic patient population"""
    print("👥 Creating patient population...")

    # Get occupied beds
    occupied_beds = db.query(Bed).filter(Bed.status == "occupied").all()
    departments = {dept.name: dept for dept in db.query(Department).all()}
    staff_by_dept = {}

    # Group staff by department
    for staff in db.query(Staff).filter(Staff.role == "doctor").all():
        dept_name = next((d.name for d in departments.values() if d.id == staff.department_id), "General Medicine")
        if dept_name not in staff_by_dept:
            staff_by_dept[dept_name] = []
        staff_by_dept[dept_name].append(staff)

    # Common names for realistic patients
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
        "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young"
    ]

    patient_counter = 1

    for bed in occupied_beds:
        # Select appropriate condition based on ward
        ward_conditions = [c for c in MEDICAL_CONDITIONS if c["typical_ward"] == bed.ward]
        if not ward_conditions:
            ward_conditions = [c for c in MEDICAL_CONDITIONS if c["severity"] == "stable"]

        condition_data = random.choice(ward_conditions)

        # Get appropriate doctor
        ward_doctors = staff_by_dept.get(bed.ward, [])
        attending_doctor = random.choice(ward_doctors) if ward_doctors else None

        # Generate realistic patient data
        age = random.randint(18, 95)
        if bed.ward == "Pediatrics":
            age = random.randint(0, 17)
        elif bed.ward == "Maternity":
            age = random.randint(16, 45)

        patient = Patient(
            patient_id=f"P{patient_counter:06d}",
            name=f"{random.choice(first_names)} {random.choice(last_names)}",
            age=age,
            gender=random.choice(["Male", "Female"]),
            date_of_birth=datetime.now() - timedelta(days=age * 365 + random.randint(0, 365)),
            phone=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            emergency_contact=f"{random.choice(first_names)} {random.choice(last_names)}",
            emergency_phone=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            insurance_id=f"INS{random.randint(100000, 999999)}",
            primary_condition=condition_data["condition"],
            severity=condition_data["severity"],
            admission_date=bed.admission_time or datetime.now(),
            expected_discharge_date=bed.expected_discharge,
            attending_physician=attending_doctor.name if attending_doctor else "Dr. On-Call",
            current_bed_id=bed.id,
            status="admitted",
            allergies=json.dumps(random.sample(["Penicillin", "Latex", "Shellfish", "Peanuts", "None"], k=random.randint(0, 2))),
            medications=json.dumps([f"Medication-{i}" for i in range(random.randint(1, 4))]),
            diet_restrictions=random.choice(["None", "Diabetic", "Low Sodium", "Soft Diet", "NPO"]),
            mobility_status=random.choice(["Ambulatory", "Wheelchair", "Bedbound"]),
            isolation_required=bed.isolation_required,
            notes=f"Patient admitted to {bed.ward} with {condition_data['condition']}"
        )

        # Update bed with patient ID
        bed.patient_id = patient.patient_id

        db.add(patient)
        patient_counter += 1

    db.commit()
    print(f"✅ Created {patient_counter - 1} patients")

def create_medical_equipment(db: Session):
    """Create medical equipment inventory"""
    print("🏥 Creating medical equipment...")

    equipment_types = [
        {"type": "Ventilator", "count": 50, "locations": ["ICU", "Emergency"]},
        {"type": "Cardiac Monitor", "count": 200, "locations": ["ICU", "Cardiology", "Emergency"]},
        {"type": "Infusion Pump", "count": 300, "locations": ["ICU", "General Medicine", "Surgery"]},
        {"type": "Defibrillator", "count": 25, "locations": ["ICU", "Emergency", "Cardiology"]},
        {"type": "X-Ray Machine", "count": 8, "locations": ["Emergency", "Orthopedics"]},
        {"type": "Ultrasound", "count": 15, "locations": ["Maternity", "Cardiology", "Emergency"]},
        {"type": "Dialysis Machine", "count": 12, "locations": ["ICU", "General Medicine"]},
        {"type": "Anesthesia Machine", "count": 20, "locations": ["Surgery"]},
        {"type": "Fetal Monitor", "count": 25, "locations": ["Maternity"]},
        {"type": "Wheelchair", "count": 100, "locations": ["All"]}
    ]

    equipment_counter = 1

    for eq_type in equipment_types:
        for i in range(eq_type["count"]):
            location = random.choice(eq_type["locations"]) if eq_type["locations"] != ["All"] else random.choice([d["name"] for d in DEPARTMENTS])

            equipment = Equipment(
                equipment_id=f"EQ{equipment_counter:06d}",
                name=f"{eq_type['type']} #{i+1}",
                equipment_type=eq_type["type"],
                manufacturer=random.choice(["Philips", "GE Healthcare", "Siemens", "Medtronic", "Abbott"]),
                model=f"Model-{random.randint(1000, 9999)}",
                serial_number=f"SN{random.randint(100000, 999999)}",
                current_location=location,
                status=random.choices(
                    ["available", "in_use", "maintenance", "broken"],
                    weights=[0.7, 0.25, 0.04, 0.01]
                )[0],
                last_maintenance=datetime.now() - timedelta(days=random.randint(1, 90)),
                next_maintenance=datetime.now() + timedelta(days=random.randint(30, 180)),
                purchase_date=datetime.now() - timedelta(days=random.randint(365, 3650)),
                cost=random.randint(5000, 500000),
                notes=f"{eq_type['type']} located in {location}"
            )

            db.add(equipment)
            equipment_counter += 1

    db.commit()
    print(f"✅ Created {equipment_counter - 1} pieces of medical equipment")

def main():
    """Main function to enrich hospital database"""
    print("🏥 HOSPITAL DATABASE ENRICHMENT")
    print("=" * 50)

    # Create tables
    create_tables()
    print("✅ Database tables ready")

    # Get database session
    db = SessionLocal()

    try:
        # Clear existing data
        clear_existing_data(db)

        # Create comprehensive data
        create_departments(db)
        create_comprehensive_staff(db)
        create_comprehensive_beds(db)
        create_realistic_patients(db)
        create_medical_equipment(db)

        # Print final summary
        print("\n🎉 DATABASE ENRICHMENT COMPLETED!")
        print("=" * 50)
        print(f"📊 FINAL STATISTICS:")
        print(f"   • Departments: {db.query(Department).count()}")
        print(f"   • Beds: {db.query(Bed).count()}")
        print(f"   • Doctors: {db.query(Staff).filter(Staff.role == 'doctor').count()}")
        print(f"   • Nurses: {db.query(Staff).filter(Staff.role == 'nurse').count()}")
        print(f"   • Patients: {db.query(Patient).count()}")
        print(f"   • Equipment: {db.query(Equipment).count()}")

        # Occupancy statistics
        total_beds = db.query(Bed).count()
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        occupancy_rate = (occupied_beds / total_beds) * 100 if total_beds > 0 else 0

        print(f"\n🏥 HOSPITAL STATUS:")
        print(f"   • Total Beds: {total_beds}")
        print(f"   • Occupied: {occupied_beds}")
        print(f"   • Occupancy Rate: {occupancy_rate:.1f}%")
        print(f"   • Available: {total_beds - occupied_beds}")

        print(f"\n🌐 Ready for testing at: http://localhost:3000")

    except Exception as e:
        print(f"❌ Error enriching database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
