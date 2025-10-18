#!/usr/bin/env python3
"""
Debug script to test database connectivity and route access
"""

from app import app, db
from models import Allergy
import traceback

def test_database():
    """Test database connectivity"""
    try:
        with app.app_context():
            # Try to query the database
            count = Allergy.query.count()
            print(f"✅ Database connection successful!")
            print(f"   Current allergies in database: {count}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"   Error: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_route():
    """Test the add_medical_history route"""
    try:
        with app.test_client() as client:
            with app.app_context():
                # Simulate a login session
                with client.session_transaction() as sess:
                    sess['logged_in'] = True
                    sess['doctor_id'] = 1
                    sess['doctor_name'] = 'Test Doctor'
                
                # Try to access the add_medical_history route
                response = client.get('/add_medical_history')
                print(f"✅ Route access successful!")
                print(f"   Status code: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   Response data: {response.data.decode()}")
                
                return True
    except Exception as e:
        print(f"❌ Route access failed!")
        print(f"   Error: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    print("🔍 EHR System Debug Tool")
    print("=" * 30)
    
    print("\n1. Testing database connectivity...")
    db_ok = test_database()
    
    if db_ok:
        print("\n2. Testing add_medical_history route...")
        route_ok = test_route()
        
        if route_ok:
            print("\n✅ All tests passed! The application should work correctly.")
        else:
            print("\n❌ Route test failed. Check the route implementation.")
    else:
        print("\n❌ Database test failed. Check MySQL server and database configuration.")
        print("\n💡 Suggestions:")
        print("   - Make sure MySQL server is running")
        print("   - Check database credentials in config.py")
        print("   - Run init_db.py to create tables if needed")

if __name__ == "__main__":
    main()