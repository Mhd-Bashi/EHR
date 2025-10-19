#!/usr/bin/env python3
"""
Database migration script to update the social_history table:
- Change smoking_status from String(50) to Boolean
- Add smoking_units String(50) column
"""

from flask import Flask
from models import db, SocialHistory
from config import Config
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def migrate_social_history():
    """Update the social_history table structure"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we need to run the migration
            print("🔍 Checking current social_history table structure...")
            
            # Try to execute a query to see current column types
            result = db.session.execute("PRAGMA table_info(social_history)")
            columns = result.fetchall()
            
            print("📋 Current columns:")
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
            
            # Check if smoking_units column already exists
            column_names = [col[1] for col in columns]
            
            if 'smoking_units' not in column_names:
                print("➕ Adding smoking_units column...")
                db.session.execute("ALTER TABLE social_history ADD COLUMN smoking_units VARCHAR(50)")
                db.session.commit()
                print("✅ Added smoking_units column")
            else:
                print("ℹ️  smoking_units column already exists")
            
            # For SQLite, we need to recreate the table to change column type
            # Let's check if there's any data first
            existing_records = db.session.execute("SELECT COUNT(*) FROM social_history").scalar()
            print(f"📊 Found {existing_records} existing social history records")
            
            if existing_records > 0:
                print("⚠️  Converting existing smoking_status data...")
                # Get all records and convert smoking_status
                records = db.session.execute("""
                    SELECT id, patient_id, smoking_status, alcohol_use, drug_use, occupation, smoking_units 
                    FROM social_history
                """).fetchall()
                
                # Convert string values to boolean
                updates = []
                for record in records:
                    old_smoking_status = record[2]  # smoking_status
                    # Convert string to boolean
                    if isinstance(old_smoking_status, str):
                        if old_smoking_status.lower() in ['true', 'yes', '1', 'smoker', 'smoking']:
                            new_smoking_status = 1
                        else:
                            new_smoking_status = 0
                    else:
                        new_smoking_status = 1 if old_smoking_status else 0
                    
                    updates.append((new_smoking_status, record[0]))  # (new_value, id)
                
                # Update records
                for new_status, record_id in updates:
                    db.session.execute(
                        "UPDATE social_history SET smoking_status = ? WHERE id = ?",
                        (new_status, record_id)
                    )
                
                db.session.commit()
                print(f"✅ Updated {len(updates)} records with boolean smoking_status")
            
            print("🎉 Social history migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Starting social history migration...")
    
    if migrate_social_history():
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)