#!/usr/bin/env python3
"""
Database initialization script that recreates all tables with correct schema
"""
from app import app
from models import db


def recreate_database():
    """Drop and recreate all database tables to fix schema issues"""
    try:
        with app.app_context():
            print("🗑️  Dropping existing tables...")
            db.drop_all()
            print("✅ All tables dropped successfully!")
            
            print("🏗️  Creating new tables with updated schema...")
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print existing tables for verification
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables in database: {tables}")
            
            # Print patient table schema
            try:
                columns = inspector.get_columns('patient')
                print("👤 Patient table columns:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            except Exception:
                print("⚠️  Could not retrieve patient table schema")
            
    except Exception as e:
        print(f"❌ Error recreating database tables: {e}")
        print("💡 Make sure your database connection is configured correctly in config.py")


def init_database():
    """Initialize the database and create all tables (without dropping existing ones)"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print existing tables for verification
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables in database: {tables}")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--recreate":
        recreate_database()
    else:
        print("🔧 To fix schema issues, run: python setup_db.py --recreate")
        print("⚠️  WARNING: --recreate will delete all existing data!")
        print("🏗️  Running normal table creation...")
        init_database()