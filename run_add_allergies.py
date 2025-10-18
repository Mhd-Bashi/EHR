from app import app, db
from models import Allergy

# Common allergies list
allergies_data = [
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

# Add allergies to database
with app.app_context():
    print("Adding allergies to database...")
    added = 0
    
    for name, description in allergies_data:
        existing = Allergy.query.filter_by(name=name).first()
        if not existing:
            allergy = Allergy(name=name, description=description)
            db.session.add(allergy)
            added += 1
            print(f"Added: {name}")
        else:
            print(f"Exists: {name}")
    
    db.session.commit()
    print(f"\nTotal added: {added}")
    print(f"Total in database: {Allergy.query.count()}")