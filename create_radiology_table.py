from app import app
from models import db, RadiologyImaging

print("Creating radiology_imaging table...")

with app.app_context():
    db.create_all()
    print("✅ Database tables created/updated successfully!")
    
    # Check if the table was created
    inspector = db.inspect(db.engine)
    if 'radiology_imaging' in inspector.get_table_names():
        print("✅ radiology_imaging table is now available")
        
        # Show table structure
        columns = inspector.get_columns('radiology_imaging')
        print("\nTable structure:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
    else:
        print("❌ radiology_imaging table was not created")