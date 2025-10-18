#!/usr/bin/env python3
"""
Simple script to delete unconfirmed doctors
"""

from app import app, db
from models import Doctor

with app.app_context():
    try:
        # Find unconfirmed doctors
        unconfirmed_doctors = Doctor.query.filter_by(email_confirmed=False).all()
        
        print(f"Found {len(unconfirmed_doctors)} unconfirmed doctors:")
        
        for doctor in unconfirmed_doctors:
            print(f"- {doctor.first_name} {doctor.last_name} ({doctor.email})")
        
        if unconfirmed_doctors:
            # Delete unconfirmed doctors
            deleted_count = Doctor.query.filter_by(email_confirmed=False).delete()
            db.session.commit()
            
            print(f"\nDeleted {deleted_count} unconfirmed doctors successfully!")
            
            # Show remaining doctors
            remaining = Doctor.query.all()
            print(f"Remaining doctors: {len(remaining)}")
            
            for doctor in remaining:
                status = "Confirmed" if doctor.email_confirmed else "Not confirmed"
                print(f"- {doctor.first_name} {doctor.last_name} ({doctor.email}) - {status}")
        else:
            print("No unconfirmed doctors to delete.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()