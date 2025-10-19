"""
Script to initialize default specialties in the database
"""

from app import app
from models import db, Specialty


def setup_default_specialties():
    """Add default specialties to the database"""

    default_specialties = [
        "General Practitioner",
        "Cardiology",
        "Dermatology",
        "Neurology",
        "Pediatrics",
        "Radiology",
        "Other",
    ]

    with app.app_context():
        # Create all tables
        db.create_all()

        # Add specialties if they don't exist
        for specialty_name in default_specialties:
            existing = Specialty.query.filter_by(name=specialty_name).first()
            if not existing:
                specialty = Specialty(name=specialty_name)
                db.session.add(specialty)
                print(f"Added specialty: {specialty_name}")
            else:
                print(f"Specialty already exists: {specialty_name}")

        # Commit changes
        try:
            db.session.commit()
            print("✅ Default specialties setup completed!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error setting up specialties: {e}")


if __name__ == "__main__":
    setup_default_specialties()
