#!/usr/bin/env python3
"""
Test database connection and check social_history table structure
"""

from flask import Flask
from models import db
from config import Config
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    try:
        print("🔍 Testing database connection...")
        
        # Test connection
        result = db.session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Check table structure
        result = db.session.execute(text("DESCRIBE social_history"))
        columns = result.fetchall()
        
        print("\n📋 Current social_history table structure:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        # Count records
        count = db.session.execute(text("SELECT COUNT(*) FROM social_history")).scalar()
        print(f"\n📊 Records in social_history: {count}")
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        import traceback
        traceback.print_exc()