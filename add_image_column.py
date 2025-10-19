from app import app
from models import db

print("Adding image_filename column to radiology_imaging table...")

with app.app_context():
    try:
        # Check if column already exists
        inspector = db.inspect(db.engine)
        if 'radiology_imaging' in inspector.get_table_names():
            columns = inspector.get_columns('radiology_imaging')
            column_names = [col['name'] for col in columns]
            
            if 'image_filename' in column_names:
                print("✅ Column image_filename already exists in radiology_imaging table")
            else:
                # Add the new column to the existing table using text() for raw SQL
                from sqlalchemy import text
                with db.engine.connect() as connection:
                    connection.execute(text("""
                        ALTER TABLE radiology_imaging 
                        ADD COLUMN image_filename VARCHAR(255) NULL
                    """))
                    connection.commit()
                
                print("✅ Successfully added image_filename column to radiology_imaging table!")
        else:
            print("❌ radiology_imaging table does not exist. Please run create_radiology_table.py first.")
            exit(1)
        
        # Verify the final table structure
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('radiology_imaging')
        print("\nFinal table structure:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
            
    except Exception as e:
        if "Duplicate column name" in str(e) or "already exists" in str(e):
            print("✅ Column image_filename already exists in radiology_imaging table")
            
            # Show current table structure
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('radiology_imaging')
            print("\nCurrent table structure:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        else:
            print(f"❌ Error adding column: {e}")
            print("This might be because the radiology_imaging table doesn't exist yet.")
            print("Try running: python create_radiology_table.py first")