#!/usr/bin/env python3
"""
Script to add common allergies and medical conditions to the database
"""

from app import app, db
from models import Allergy


def add_common_allergies():
    """Add 10 most common allergies/conditions plus 'Other' option"""

    common_allergies = [
        {
            "name": "Penicillin",
            "description": ("Antibiotic allergy that can cause skin rash, "
                            "hives, swelling, or in severe cases, anaphylaxis. "
                            "Requires alternative antibiotics.")
        },
        {
            "name": "Peanuts",
            "description": ("Food allergy that can range from mild digestive symptoms "
                            "to severe anaphylactic reactions. Requires strict avoidance.",),
        },
        {
            "name": "Shellfish",
            "description": ("Food allergy to crustaceans and mollusks that can cause "
                            "reactions ranging from mild to life-threatening anaphylaxis."),
        },
        {
            "name": "Dust Mites",
            "description": ("Environmental allergy causing respiratory symptoms like "
                            "sneezing, runny nose, and asthma symptoms."),
        },
        {
            "name": "Pollen",
            "description": ("Seasonal environmental allergy causing hay fever symptoms including "
                            "sneezing, itchy eyes, and nasal congestion."),
        },
        {
            "name": "Latex",
            "description": ("Contact allergy to natural rubber latex causing skin reactions and "
                            "potentially severe systemic reactions."),
        },
        {
            "name": "Sulfa Drugs",
            "description": ("Medication allergy to sulfonamide antibiotics that can cause skin rashes, "
                            "fever, or more serious reactions."),
        },
        {
            "name": "Aspirin",
            "description": ("Medication allergy that can cause respiratory symptoms, "
                            "skin reactions, or gastrointestinal issues."),
        },
        {
            "name": "Eggs",
            "description": ("Food allergy common in children that can cause digestive "
                            " symptoms, skin reactions, or respiratory issues."),
        },
        {
            "name": "Dairy/Milk",
            "description": ("Food allergy to milk proteins that can cause digestive "
                            "symptoms,skin reactions, or respiratory issues."),
        },
        {
            "name": "Other",
            "description": ("For allergies or medical conditions not listed above. "
                            "Please specify in the description field."),
        },
    ]

    with app.app_context():
        # Check if allergies already exist
        existing_count = Allergy.query.count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} allergies.")
            overwrite = (
                input("Do you want to add more allergies anyway? (y/n): ")
                .lower()
                .strip()
            )
            if overwrite != "y":
                print("Operation cancelled.")
                return

        added_count = 0
        skipped_count = 0

        for allergy_data in common_allergies:
            # Check if this allergy already exists
            existing_allergy = Allergy.query.filter_by(
                name=allergy_data["name"]
            ).first()

            if existing_allergy:
                print(f"⚠️  Allergy '{allergy_data['name']}' already exists - skipping")
                skipped_count += 1
                continue

            # Create new allergy
            new_allergy = Allergy(
                name=allergy_data["name"], description=allergy_data["description"]
            )

            try:
                db.session.add(new_allergy)
                db.session.commit()
                print(f"✅ Added allergy: {allergy_data['name']}")
                added_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error adding allergy '{allergy_data['name']}': {str(e)}")

        print(f"\n📊 Summary:")
        print(f"   - Added: {added_count} allergies")
        print(f"   - Skipped: {skipped_count} allergies")
        print(f"   - Total in database: {Allergy.query.count()} allergies")

        if added_count > 0:
            print(f"\n🎉 Successfully populated the allergies database!")
            print(f"   You can now add medical history with these common allergies.")


def list_current_allergies():
    """List all current allergies in the database"""
    with app.app_context():
        allergies = Allergy.query.order_by(Allergy.name).all()

        if not allergies:
            print("No allergies found in the database.")
            return

        print(f"\n📋 Current allergies in database ({len(allergies)} total):")
        print("-" * 50)

        for i, allergy in enumerate(allergies, 1):
            print(f"{i:2d}. {allergy.name}")
            if allergy.description:
                print(
                    f"{allergy.description[:100]}{'...' if len(allergy.description) > 100 else ''}"
                )
            print()


def main():
    """Main function with menu options"""
    print("🏥 EHR System - Allergy Database Setup")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Add common allergies to database")
        print("2. List current allergies in database")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            add_common_allergies()
        elif choice == "2":
            list_current_allergies()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
