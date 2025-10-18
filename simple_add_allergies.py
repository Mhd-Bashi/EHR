#!/usr/bin/env python3
"""
Simple script to add common allergies to the database
"""

from app import app, db
from models import Allergy


def add_allergies():
    """Add common allergies to the database"""
    
    common_allergies = [
        ("Penicillin", "Antibiotic allergy - can cause rash, hives, or anaphylaxis"),
        ("Peanuts", "Food allergy - can cause severe reactions, requires avoidance"),
        ("Shellfish", "Food allergy - can cause mild to severe reactions"),
        ("Dust Mites", "Environmental allergy - causes respiratory symptoms"),
        ("Pollen", "Seasonal allergy - causes hay fever symptoms"),
        ("Latex", "Contact allergy - causes skin and systemic reactions"),
        ("Sulfa Drugs", "Medication allergy - can cause skin rashes and fever"),
        ("Aspirin", "Medication allergy - causes respiratory or skin reactions"),
        ("Eggs", "Food allergy - common in children, various symptoms"),
        ("Dairy/Milk", "Food allergy - causes digestive and skin reactions"),
        ("Other", "For allergies not listed above - specify in description")
    ]
    
    with app.app_context():
        added_count = 0
        
        for name, description in common_allergies:
            # Check if allergy already exists
            existing = Allergy.query.filter_by(name=name).first()
            
            if existing:
                print(f"Skipping {name} - already exists")
                continue
            
            # Create new allergy
            new_allergy = Allergy(name=name, description=description)
            
            try:
                db.session.add(new_allergy)
                db.session.commit()
                print(f"Added: {name}")
                added_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"Error adding {name}: {str(e)}")
        
        print(f"\nAdded {added_count} new allergies to the database.")
        print(f"Total allergies in database: {Allergy.query.count()}")


if __name__ == "__main__":
    add_allergies()