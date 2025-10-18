#!/usr/bin/env python3
"""
Fix lab results with invalid date formats
"""

from app import app, db
from models import LaboratoryResult
from datetime import datetime


def fix_lab_results_dates():
    """Fix any lab results that have string dates instead of datetime objects"""
    
    with app.app_context():
        print("Checking lab results for date format issues...")
        
        try:
            # Get all lab results
            lab_results = LaboratoryResult.query.all()
            print(f"Found {len(lab_results)} lab results")
            
            fixed_count = 0
            for result in lab_results:
                print(f"Lab Result ID {result.id}: date = {result.date}, type = {type(result.date)}")
                
                # If the date is a string, try to convert it
                if isinstance(result.date, str):
                    try:
                        # Try different date formats
                        for date_format in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]:
                            try:
                                new_date = datetime.strptime(result.date, date_format)
                                result.date = new_date
                                print(f"  ✓ Fixed: {result.date} -> {new_date}")
                                fixed_count += 1
                                break
                            except ValueError:
                                continue
                        else:
                            print(f"  ✗ Could not parse date: {result.date}")
                    except Exception as e:
                        print(f"  ✗ Error fixing date: {e}")
            
            if fixed_count > 0:
                db.session.commit()
                print(f"\n✅ Fixed {fixed_count} lab result dates")
            else:
                print("\n✅ No date fixes needed")
                
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error checking lab results: {e}")
            return False


if __name__ == "__main__":
    fix_lab_results_dates()