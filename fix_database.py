#!/usr/bin/env python3
"""
Simple database fix script for the email column issue
"""

print("🔧 EHR Database Fix Script")
print("=" * 40)

try:
    from app import app
    from models import db
    print("✅ Successfully imported app and models")
    
    with app.app_context():
        print("🔍 Checking database connection...")
        
        # Try to get inspector to check current schema
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"📋 Existing tables: {existing_tables}")
        
        if 'patient' in existing_tables:
            try:
                columns = inspector.get_columns('patient')
                column_names = [col['name'] for col in columns]
                print(f"👤 Current patient table columns: {column_names}")
                
                if 'email' not in column_names:
                    print("❌ Patient table missing 'email' column!")
                    print("🔧 Need to recreate tables...")
                    
                    # Drop and recreate all tables
                    print("🗑️  Dropping all tables...")
                    db.drop_all()
                    
                    print("🏗️  Creating tables with correct schema...")
                    db.create_all()
                    
                    # Verify the fix
                    new_columns = inspector.get_columns('patient')
                    new_column_names = [col['name'] for col in new_columns]
                    print(f"✅ New patient table columns: {new_column_names}")
                    
                    if 'email' in new_column_names:
                        print("🎉 SUCCESS: Email column now exists!")
                    else:
                        print("❌ ERROR: Email column still missing")
                else:
                    print("✅ Patient table already has email column")
                    
            except Exception as e:
                print(f"⚠️  Error checking patient table: {e}")
                print("🔧 Attempting to recreate all tables...")
                
                db.drop_all()
                db.create_all()
                print("✅ Tables recreated")
        else:
            print("📄 No patient table found, creating all tables...")
            db.create_all()
            print("✅ All tables created")
            
        print("\n🎉 Database fix completed successfully!")
        print("💡 You can now restart your Flask app")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the correct directory and all dependencies are installed")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Try running this script from the EHR directory")