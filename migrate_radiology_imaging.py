#!/usr/bin/env python3
"""
Migration script to create the radiology_imaging table
This script creates a new table similar to laboratory_result but for radiology imaging records
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import RadiologyImaging


def create_radiology_imaging_table():
    """Create the radiology_imaging table in the database"""
    
    with app.app_context():
        try:
            # Check if table already exists
            inspector = db.inspect(db.engine)
            if 'radiology_imaging' in inspector.get_table_names():
                print("✅ Table 'radiology_imaging' already exists")
                return True
            
            print("Creating radiology_imaging table...")
            
            # Create the table
            db.create_all()
            
            # Verify table was created
            inspector = db.inspect(db.engine)
            if 'radiology_imaging' in inspector.get_table_names():
                print("✅ Successfully created radiology_imaging table")
                
                # Print table structure
                columns = inspector.get_columns('radiology_imaging')
                print("\nTable structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                return True
            else:
                print("❌ Failed to create radiology_imaging table")
                return False
                
        except Exception as e:
            print(f"❌ Error creating radiology_imaging table: {str(e)}")
            return False


def add_sample_data():
    """Add some sample radiology imaging records for testing"""
    
    with app.app_context():
        try:
            # Check if we have any patients to work with
            from models import Patient
            patients = Patient.query.limit(3).all()
            
            if not patients:
                print("No patients found - skipping sample data creation")
                return True
            
            print(f"Adding sample radiology imaging records for {len(patients)} patients...")
            
            sample_imaging = [
                {"name": "Chest X-Ray", "date": datetime(2024, 10, 15, 9, 0)},
                {"name": "MRI Brain", "date": datetime(2024, 10, 10, 14, 30)},
                {"name": "CT Scan Abdomen", "date": datetime(2024, 10, 5, 11, 15)},
                {"name": "Ultrasound Pelvis", "date": datetime(2024, 10, 1, 16, 45)},
                {"name": "Mammography", "date": datetime(2024, 9, 28, 10, 30)},
                {"name": "Bone Scan", "date": datetime(2024, 9, 25, 13, 0)},
            ]
            
            # Add 2 imaging records per patient
            for i, patient in enumerate(patients):
                for j in range(2):
                    imaging_index = (i * 2 + j) % len(sample_imaging)
                    imaging_data = sample_imaging[imaging_index]
                    
                    radiology_record = RadiologyImaging(
                        patient_id=patient.id,
                        name=imaging_data["name"],
                        date=imaging_data["date"]
                    )
                    
                    db.session.add(radiology_record)
            
            db.session.commit()
            
            # Verify data was added
            count = RadiologyImaging.query.count()
            print(f"✅ Successfully added {count} sample radiology imaging records")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding sample data: {str(e)}")
            return False


def main():
    """Main migration function"""
    print("🏥 Starting Radiology Imaging Table Migration")
    print("=" * 50)
    
    # Create the table
    if not create_radiology_imaging_table():
        print("❌ Migration failed")
        sys.exit(1)
    
    # Add sample data
    print("\n" + "=" * 50)
    if not add_sample_data():
        print("⚠️  Table created but sample data failed")
    
    print("\n" + "=" * 50)
    print("🎉 Migration completed successfully!")
    print("\nNew table 'radiology_imaging' is ready for use.")
    print("Fields: id, patient_id, name, date, created_at, updated_at")


if __name__ == "__main__":
    main()