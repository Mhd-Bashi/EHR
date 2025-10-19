#!/usr/bin/env python3
"""
MySQL Database migration script to update the social_history table:
- Add smoking_units VARCHAR(50) column
- Update smoking_status from VARCHAR(50) to BOOLEAN/TINYINT(1)
"""

from flask import Flask
from models import db
from config import Config
import sys
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def migrate_social_history_mysql():
    """Update the social_history table structure for MySQL"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking current social_history table structure...")
            
            # Check current table structure
            result = db.session.execute(text("DESCRIBE social_history"))
            columns = result.fetchall()
            
            print("📋 Current columns:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            # Check if smoking_units column exists
            column_names = [col[0] for col in columns]
            
            # Add smoking_units column if it doesn't exist
            if 'smoking_units' not in column_names:
                print("➕ Adding smoking_units column...")
                db.session.execute(text("ALTER TABLE social_history ADD COLUMN smoking_units VARCHAR(50)"))
                db.session.commit()
                print("✅ Added smoking_units column")
            else:
                print("ℹ️  smoking_units column already exists")
            
            # Check current data and convert smoking_status to boolean
            existing_records = db.session.execute(text("SELECT COUNT(*) FROM social_history")).scalar()
            print(f"📊 Found {existing_records} existing social history records")
            
            if existing_records > 0:
                print("⚠️  Converting existing smoking_status data to boolean...")
                
                # Get all records
                records = db.session.execute(text("""
                    SELECT id, smoking_status 
                    FROM social_history
                """)).fetchall()
                
                # Convert string values to boolean (0 or 1 for MySQL)
                for record in records:
                    record_id, old_smoking_status = record[0], record[1]
                    
                    # Convert to boolean (0 or 1)
                    if old_smoking_status:
                        if isinstance(old_smoking_status, str):
                            if old_smoking_status.lower() in ['true', 'yes', '1', 'smoker', 'smoking']:
                                new_smoking_status = 1
                            else:
                                new_smoking_status = 0
                        elif old_smoking_status:
                            new_smoking_status = 1
                        else:
                            new_smoking_status = 0
                    else:
                        new_smoking_status = 0
                    
                    # Update the record
                    db.session.execute(
                        text("UPDATE social_history SET smoking_status = :new_status WHERE id = :record_id"),
                        {"new_status": new_smoking_status, "record_id": record_id}
                    )
                
                db.session.commit()
                print(f"✅ Updated {len(records)} records with boolean smoking_status")
            
            # Now alter the column type to TINYINT(1) for proper boolean
            print("🔄 Converting smoking_status column to TINYINT(1)...")
            try:
                db.session.execute(text("ALTER TABLE social_history MODIFY COLUMN smoking_status TINYINT(1) DEFAULT 0"))
                db.session.commit()
                print("✅ Converted smoking_status to TINYINT(1)")
            except Exception as e:
                print(f"⚠️  Note: Column type conversion might need manual intervention: {e}")
            
            print("🎉 Social history migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting MySQL social history migration...")
    
    if migrate_social_history_mysql():
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)