#!/usr/bin/env python3
"""
Script to delete all doctors with email_confirmed=0
"""

from app import app, db
from models import Doctor


def delete_unconfirmed_doctors():
    """Delete all doctors with email_confirmed=0 and their related data"""

    with app.app_context():
        try:
            # Import additional models for cleanup
            from models import Patient, Appointment, MedicalHistory, LaboratoryResult

            # First, let's see how many doctors have email_confirmed=0
            unconfirmed_doctors = Doctor.query.filter_by(email_confirmed=False).all()

            if not unconfirmed_doctors:
                print("✅ No unconfirmed doctors found in the database.")
                return

            print(f"📋 Found {len(unconfirmed_doctors)} unconfirmed doctors:")
            print("-" * 60)

            total_patients = 0
            total_appointments = 0
            total_lab_results = 0
            total_medical_history = 0

            for doctor in unconfirmed_doctors:
                # Count related records for this doctor
                patients = Patient.query.filter_by(doctor_id=doctor.id).all()
                patient_count = len(patients)
                total_patients += patient_count

                appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
                appointment_count = len(appointments)
                total_appointments += appointment_count

                # Count lab results and medical history for this doctor's patients
                lab_results = 0
                medical_history = 0
                for patient in patients:
                    lab_results += LaboratoryResult.query.filter_by(
                        patient_id=patient.id
                    ).count()
                    medical_history += MedicalHistory.query.filter_by(
                        patient_id=patient.id
                    ).count()

                total_lab_results += lab_results
                total_medical_history += medical_history

                print(
                    f"ID: {doctor.id} | Name: {doctor.first_name} {doctor.last_name} | Email: {doctor.email}"
                )
                print(
                    f"   Patients: {patient_count}, Appointments: {appointment_count}, Lab Results: {lab_results}, Medical History: {medical_history}"
                )

            print("-" * 60)
            print(f"📊 Total records to be deleted:")
            print(f"   Doctors: {len(unconfirmed_doctors)}")
            print(f"   Patients: {total_patients}")
            print(f"   Appointments: {total_appointments}")
            print(f"   Lab Results: {total_lab_results}")
            print(f"   Medical History: {total_medical_history}")
            print("-" * 60)

            # Ask for confirmation
            confirm_msg = f"\n⚠️  Are you sure you want to delete these {len(unconfirmed_doctors)} unconfirmed doctors and ALL their related data? (yes/no): "
            confirm = input(confirm_msg).lower().strip()

            if confirm == "yes":
                deleted_doctors = 0
                deleted_patients = 0
                deleted_appointments = 0
                deleted_lab_results = 0
                deleted_medical_history = 0

                print("\n🔄 Starting deletion process...")

                for doctor in unconfirmed_doctors:
                    print(
                        f"   Processing doctor: {doctor.first_name} {doctor.last_name}"
                    )

                    # Get all patients for this doctor
                    patients = Patient.query.filter_by(doctor_id=doctor.id).all()

                    for patient in patients:
                        # Delete lab results for this patient
                        lab_count = LaboratoryResult.query.filter_by(
                            patient_id=patient.id
                        ).delete()
                        deleted_lab_results += lab_count

                        # Delete medical history for this patient
                        history_count = MedicalHistory.query.filter_by(
                            patient_id=patient.id
                        ).delete()
                        deleted_medical_history += history_count

                    # Delete appointments for this doctor
                    appointment_count = Appointment.query.filter_by(
                        doctor_id=doctor.id
                    ).delete()
                    deleted_appointments += appointment_count

                    # Delete patients for this doctor
                    patient_count = Patient.query.filter_by(
                        doctor_id=doctor.id
                    ).delete()
                    deleted_patients += patient_count

                    # Clear doctor-specialty relationships
                    doctor.specialties.clear()

                    deleted_doctors += 1

                # Finally, delete the doctors themselves
                Doctor.query.filter_by(email_confirmed=False).delete()

                # Commit all changes
                db.session.commit()

                print(f"✅ Successfully deleted:")
                print(f"   Doctors: {deleted_doctors}")
                print(f"   Patients: {deleted_patients}")
                print(f"   Appointments: {deleted_appointments}")
                print(f"   Lab Results: {deleted_lab_results}")
                print(f"   Medical History: {deleted_medical_history}")

                # Show remaining doctors
                remaining_doctors = Doctor.query.all()
                print(f"\n📊 Remaining doctors in database: {len(remaining_doctors)}")

                if remaining_doctors:
                    print("\n👥 Remaining confirmed doctors:")
                    for doctor in remaining_doctors:
                        status = (
                            "✅ Confirmed"
                            if doctor.email_confirmed
                            else "❌ Not confirmed"
                        )
                        print(
                            f"   {doctor.first_name} {doctor.last_name} ({doctor.email}) - {status}"
                        )

            else:
                print("❌ Operation cancelled. No doctors were deleted.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting doctors: {str(e)}")
            import traceback

            print(f"📝 Full error details:\n{traceback.format_exc()}")


def show_all_doctors():
    """Show all doctors and their confirmation status"""

    with app.app_context():
        try:
            doctors = Doctor.query.all()

            if not doctors:
                print("📋 No doctors found in the database.")
                return

            print(f"📋 All doctors in database ({len(doctors)} total):")
            print("-" * 80)

            confirmed_count = 0
            unconfirmed_count = 0

            for doctor in doctors:
                status = (
                    "✅ Confirmed" if doctor.email_confirmed else "❌ Not confirmed"
                )
                print(
                    f"ID: {doctor.id:2d} | {doctor.first_name} {doctor.last_name:15s} | {doctor.email:30s} | {status}"
                )

                if doctor.email_confirmed:
                    confirmed_count += 1
                else:
                    unconfirmed_count += 1

            print("-" * 80)
            print(
                f"📊 Summary: {confirmed_count} confirmed, {unconfirmed_count} unconfirmed"
            )

        except Exception as e:
            print(f"❌ Error retrieving doctors: {str(e)}")


def main():
    """Main function with menu options"""
    print("🏥 EHR System - Doctor Management Tool")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Show all doctors and their confirmation status")
        print("2. Delete all unconfirmed doctors (email_confirmed=0)")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            show_all_doctors()
        elif choice == "2":
            delete_unconfirmed_doctors()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
