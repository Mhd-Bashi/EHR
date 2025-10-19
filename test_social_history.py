#!/usr/bin/env python3
"""
Test script to verify social history integration is working
"""

from flask import Flask
from models import db, Patient, SocialHistory
from config import Config

def test_social_history():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test if we can query social history
            social_histories = SocialHistory.query.all()
            print(f"📊 Found {len(social_histories)} social history records")
            
            # Test if patient relationship works
            patients_with_social = Patient.query.filter(Patient.social_history.isnot(None)).all()
            print(f"👥 Found {len(patients_with_social)} patients with social history")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🧪 Testing social history integration...")
    if test_social_history():
        print("✅ Social history integration is working!")
    else:
        print("❌ Social history integration has issues!")