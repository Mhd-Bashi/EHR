#!/usr/bin/env python3
"""
Simple migration script to add smoking_units column to existing database
This handles the MySQL database schema update safely
"""

from flask import Flask
from models import db, SocialHistory
from config import Config
from sqlalchemy import text

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def add_smoking_units_column():
    """Add the smoking_units column if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking if smoking_units column exists...")
            
            # Check if column exists in MySQL
            result = db.session.execute(text(
                "SELECT COUNT(*) as column_count FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'social_history' "
                "AND column_name = 'smoking_units'"
            ))
            
            column_exists = result.scalar() > 0
            
            if not column_exists:
                print("➕ Adding smoking_units column...")
                db.session.execute(text("ALTER TABLE social_history ADD COLUMN smoking_units VARCHAR(50)"))
                db.session.commit()
                print("✅ Successfully added smoking_units column")
            else:
                print("ℹ️  smoking_units column already exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add column: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Adding smoking_units column to social_history table...")
    
    if add_smoking_units_column():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")