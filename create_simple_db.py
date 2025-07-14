import sqlite3
import os
from datetime import datetime

def create_database():
    # Remove existing database
    if os.path.exists('hospital.db'):
        os.remove('hospital.db')
    
    # Create database
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # Create beds table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_number TEXT UNIQUE NOT NULL,
        room_number TEXT NOT NULL,
        ward TEXT NOT NULL,
        bed_type TEXT NOT NULL,
        status TEXT NOT NULL,
        patient_id TEXT,
        admission_time TEXT,
        expected_discharge TEXT,
        last_updated TEXT,
        created_at TEXT
    )
    ''')

    # Insert sample data
    now = datetime.now().isoformat()
    sample_beds = [
        ('ICU-001', '101', 'ICU', 'ICU', 'occupied', 'P001', now, None, now, now),
        ('ICU-002', '102', 'ICU', 'ICU', 'vacant', None, None, None, now, now),
        ('ICU-003', '103', 'ICU', 'ICU', 'cleaning', None, None, None, now, now),
        ('GEN-001', '201', 'General', 'General', 'occupied', 'P002', now, None, now, now),
        ('GEN-002', '202', 'General', 'General', 'vacant', None, None, None, now, now),
        ('GEN-003', '203', 'General', 'General', 'occupied', 'P003', now, None, now, now),
        ('ER-001', '301', 'Emergency', 'Emergency', 'occupied', 'P004', now, None, now, now),
        ('ER-002', '302', 'Emergency', 'Emergency', 'vacant', None, None, None, now, now),
    ]

    cursor.executemany('''
    INSERT OR REPLACE INTO beds 
    (bed_number, room_number, ward, bed_type, status, patient_id, admission_time, expected_discharge, last_updated, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_beds)

    conn.commit()
    conn.close()
    print("Database created successfully with 8 sample beds")

if __name__ == "__main__":
    create_database()
