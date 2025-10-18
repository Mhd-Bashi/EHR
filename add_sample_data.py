#!/usr/bin/env python3
"""
Script to add sample data for testing the dashboard
"""

from app import app
from models import (
    db,
    Doctor,
    Patient,
    LaboratoryResult,
    Appointment,
    AppointmentStatusEnum,
    GenderEnum,
    Allergy,
    MedicalHistory,
)
from datetime import datetime, timedelta
import random


def add_sample_data():
    """Add sample patients, lab results, and appointments"""

    with app.app_context():
        # Check if we already have sample data
        existing_patient = Patient.query.first()
        if existing_patient:
            print("Sample data already exists. Skipping...")
            return

        # Create a new doctor
        from werkzeug.security import generate_password_hash

        doctor = Doctor(
            first_name="mhd",
            last_name="bash",
            email="mhd.bash@test.com",
            username="mhd.bash",
            password=generate_password_hash("P@ssw0rd1"),
            email_confirmed=True,
            email_confirmed_at=datetime.now(),
        )
        db.session.add(doctor)
        db.session.commit()

        # Get the first confirmed doctor
        doctor = Doctor.query.filter_by(email_confirmed=True).first()

        if not doctor:
            print(
                "❌ No confirmed doctor found. Please register and confirm a doctor account first."
            )
            return

        print(f"Adding sample data for Dr. {doctor.last_name}...")

        # Sample patients
        patients_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "age": 45,
                "gender": GenderEnum.MALE,
            },
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "age": 32,
                "gender": GenderEnum.FEMALE,
            },
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "age": 67,
                "gender": GenderEnum.MALE,
            },
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "age": 29,
                "gender": GenderEnum.FEMALE,
            },
            {
                "first_name": "Robert",
                "last_name": "Wilson",
                "age": 54,
                "gender": GenderEnum.MALE,
            },
        ]

        patients = []
        for patient_data in patients_data:
            patient = Patient(
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                age=patient_data["age"],
                gender=patient_data["gender"],
                doctor_id=doctor.id,
                date_of_birth=datetime.now().date()
                - timedelta(days=patient_data["age"] * 365),
            )
            db.session.add(patient)
            patients.append(patient)

        db.session.commit()
        print(f"✅ Added {len(patients)} sample patients")

        # Sample allergies
        allergies_data = [
            {
                "name": "Penicillin",
                "description": "Antibiotic allergy - can cause rash, hives, or anaphylaxis",
            },
            {
                "name": "Peanuts",
                "description": "Food allergy - can cause severe reactions including anaphylaxis",
            },
            {
                "name": "Shellfish",
                "description": "Seafood allergy - can cause swelling, hives, and breathing difficulties",
            },
            {"name": "Latex", "description": "Contact allergy to rubber products"},
            {
                "name": "Dust Mites",
                "description": "Environmental allergy causing respiratory symptoms",
            },
            {
                "name": "Pollen",
                "description": "Seasonal allergy causing hay fever symptoms",
            },
            {
                "name": "Cat Dander",
                "description": "Pet allergy causing respiratory and skin reactions",
            },
            {"name": "Aspirin", "description": "Medication allergy - avoid NSAIDs"},
            {"name": "Sulfa Drugs", "description": "Antibiotic family allergy"},
            {
                "name": "Eggs",
                "description": "Food allergy - especially problematic in vaccines",
            },
        ]

        allergies = []
        for allergy_data in allergies_data:
            # Check if allergy already exists
            existing_allergy = Allergy.query.filter_by(
                name=allergy_data["name"]
            ).first()
            if not existing_allergy:
                allergy = Allergy(
                    name=allergy_data["name"], description=allergy_data["description"]
                )
                db.session.add(allergy)
                allergies.append(allergy)
            else:
                allergies.append(existing_allergy)

        db.session.commit()
        print(f"✅ Added {len([a for a in allergies if a.id is None])} new allergies")

        # Sample medical history entries
        medical_histories = []
        for patient in patients:
            # Add 1-3 medical history entries per patient
            num_histories = random.randint(1, 3)
            patient_allergies = random.sample(
                allergies, min(num_histories, len(allergies))
            )

            for i, allergy in enumerate(patient_allergies):
                # Create realistic descriptions based on allergy type
                if "food" in allergy.description.lower():
                    descriptions = [
                        f"Patient reported severe reaction to {allergy.name.lower()} - hives and swelling",
                        f"Confirmed {allergy.name.lower()} allergy after reaction at restaurant",
                        f"Family history of {allergy.name.lower()} allergy, patient confirmed reaction",
                    ]
                elif (
                    "medication" in allergy.description.lower()
                    or "antibiotic" in allergy.description.lower()
                ):
                    descriptions = [
                        f"Developed rash after taking {allergy.name.lower()}",
                        f"Allergic reaction to {allergy.name.lower()} during previous treatment",
                        f"Patient reports intolerance to {allergy.name.lower()} - avoid in future prescriptions",
                    ]
                else:
                    descriptions = [
                        f"Documented allergy to {allergy.name.lower()}",
                        f"Patient experiences symptoms when exposed to {allergy.name.lower()}",
                        f"Confirmed {allergy.name.lower()} allergy through testing",
                    ]

                history = MedicalHistory(
                    patient_id=patient.id,
                    allergy_id=allergy.id,
                    description=random.choice(descriptions),
                    date=datetime.now()
                    - timedelta(
                        days=random.randint(30, 1095)
                    ),  # 1 month to 3 years ago
                )
                db.session.add(history)
                medical_histories.append(history)

        db.session.commit()
        print(f"✅ Added {len(medical_histories)} medical history entries")

        # Sample lab results
        lab_tests = [
            "Complete Blood Count",
            "Blood Glucose",
            "Cholesterol Panel",
            "Liver Function",
            "Kidney Function",
            "Thyroid Function",
            "Hemoglobin A1c",
            "Vitamin D",
            "Iron Studies",
            "Lipid Panel",
        ]

        lab_results = []
        for patient in patients:
            # Add 2-4 lab results per patient
            num_results = random.randint(2, 4)
            for _ in range(num_results):
                test_name = random.choice(lab_tests)

                # Generate realistic results based on test type
                if "glucose" in test_name.lower():
                    result = f"{random.randint(80, 120)} mg/dL"
                elif "cholesterol" in test_name.lower() or "lipid" in test_name.lower():
                    result = f"Total: {random.randint(150, 250)} mg/dL"
                elif "hemoglobin" in test_name.lower():
                    result = f"{random.uniform(4.0, 8.0):.1f}%"
                elif "vitamin" in test_name.lower():
                    result = f"{random.randint(20, 50)} ng/mL"
                else:
                    result = (
                        "Normal" if random.random() > 0.3 else "Abnormal - See notes"
                    )

                lab_result = LaboratoryResult(
                    patient_id=patient.id,
                    test_name=test_name,
                    result=result,
                    date=datetime.now() - timedelta(days=random.randint(1, 90)),
                )
                db.session.add(lab_result)
                lab_results.append(lab_result)

        db.session.commit()
        print(f"✅ Added {len(lab_results)} sample lab results")

        # Sample appointments
        appointments = []
        statuses = [
            AppointmentStatusEnum.SCHEDULED,
            AppointmentStatusEnum.COMPLETED,
            AppointmentStatusEnum.CANCELLED,
        ]

        for patient in patients:
            # Add 2-3 appointments per patient
            num_appointments = random.randint(2, 3)
            for i in range(num_appointments):
                # Mix of past and future appointments
                if i == 0:  # First appointment - recent past
                    appointment_date = datetime.now() - timedelta(
                        days=random.randint(1, 30)
                    )
                    status = AppointmentStatusEnum.COMPLETED
                elif i == 1:  # Second appointment - near future
                    appointment_date = datetime.now() + timedelta(
                        days=random.randint(1, 14)
                    )
                    status = AppointmentStatusEnum.SCHEDULED
                else:  # Third appointment - random
                    appointment_date = datetime.now() + timedelta(
                        days=random.randint(-60, 60)
                    )
                    status = random.choice(statuses)

                appointment = Appointment(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    date=appointment_date,
                    status=status,
                )

                try:
                    db.session.add(appointment)
                    appointments.append(appointment)
                except Exception as e:
                    print(f"Skipping duplicate appointment: {e}")
                    db.session.rollback()

        try:
            db.session.commit()
            print(f"✅ Added {len(appointments)} sample appointments")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding appointments: {e}")

        print("✅ Sample data setup completed!")
        print(
            f"Dashboard will show data for Dr. {doctor.first_name} {doctor.last_name}"
        )


if __name__ == "__main__":
    add_sample_data()
