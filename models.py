from datetime import datetime
import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()

# --- Association table for many-to-many: Doctor <-> Specialty
doctor_specialty = db.Table(
    "doctor_specialty",
    db.Column("doctor_id", db.Integer, db.ForeignKey("doctor.id"), primary_key=True),
    db.Column("specialty_id", db.Integer, db.ForeignKey("specialty.id"), primary_key=True),
)


class Doctor(db.Model):
    __tablename__ = "doctor"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False, index=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmed_at = db.Column(db.DateTime)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # One-to-many
    patients = db.relationship(
        "Patient",
        back_populates="doctor",
        cascade="all, delete-orphan",
        lazy=True,
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # Many-to-many (doctors can share specialties; a doctor can have multiple)
    specialties = db.relationship(
        "Specialty",
        secondary=doctor_specialty,
        back_populates="doctors",
        lazy=True,
    )

    def __repr__(self):
        return f"<Doctor id={self.id} {self.first_name} {self.last_name}>"


class Specialty(db.Model):
    __tablename__ = "specialty"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # reverse side of many-to-many
    doctors = db.relationship(
        "Doctor",
        secondary=doctor_specialty,
        back_populates="specialties",
        lazy=True,
    )

    def __repr__(self):
        return f"<Specialty {self.name}>"


class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AppointmentStatusEnum(enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Patient(db.Model):
    __tablename__ = "patient"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False, index=True)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=False, nullable=True, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer)
    gender = db.Column(
        Enum(GenderEnum, name="gender_enum"),
        nullable=True
    )
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    doctor = db.relationship("Doctor", back_populates="patients")

    # One-to-one
    demographic_info = db.relationship(
        "DemographicInfo",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # One-to-one (if you truly want a single row per patient)
    social_history = db.relationship(
        "SocialHistory",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # One-to-many
    medical_histories = db.relationship(
        "MedicalHistory",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy=True,
    )

    laboratory_results = db.relationship(
        "LaboratoryResult",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy=True,
    )

    prescriptions = db.relationship(
        "Prescription",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy=True,
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy=True,
    )

    allergies = db.relationship(
        "Allergy",
        secondary="medical_history",
        viewonly=True
        )

    def __repr__(self):
        return f"<Patient id={self.id} {self.first_name} {self.last_name}>"


class Appointment(db.Model):
    __tablename__ = "appointment"

    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'date', name='uq_appointment_doctor_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)

    date = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    status = db.Column(Enum(AppointmentStatusEnum, name="appointment_status_enum"),
                       nullable=False,
                       default=AppointmentStatusEnum.SCHEDULED)

    patient = db.relationship(
        "Patient",
        back_populates="appointments"
    )
    doctor = db.relationship(
        "Doctor",
        back_populates="appointments"
    )

    def __repr__(self):
        return f"<Appointment id={self.id} on {self.date:%Y-%m-%d %H:%M}>"


class DemographicInfo(db.Model):
    __tablename__ = "demographic_info"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, unique=True)
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(100))

    patient = db.relationship(
        "Patient",
        back_populates="demographic_info"
        )

    def __repr__(self):
        return f"<DemographicInfo patient_id={self.patient_id}>"


class SocialHistory(db.Model):
    __tablename__ = "social_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, unique=True)
    smoking_status = db.Column(db.String(50))  # Keep as string for now to match existing database
    # smoking_units = db.Column(db.String(50))  # Commented out until database migration is complete
    alcohol_use = db.Column(db.String(50))
    drug_use = db.Column(db.String(50))
    occupation = db.Column(db.String(100))

    patient = db.relationship(
        "Patient",
        back_populates="social_history"
        )

    def __repr__(self):
        return f"<SocialHistory patient_id={self.patient_id}>"


class MedicalHistory(db.Model):
    __tablename__ = "medical_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    allergy_id = db.Column(db.Integer, db.ForeignKey("allergy.id"), nullable=False)

    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, index=True)

    patient = db.relationship(
        "Patient",
        back_populates="medical_histories"
        )

    allergy = db.relationship(
        "Allergy",
        back_populates="medical_histories"
        )

    def __repr__(self):
        return f"<MedicalHistory id={self.id} date={self.date:%Y-%m-%d}>"


class Allergy(db.Model):
    __tablename__ = "allergy"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

    medical_histories = db.relationship(
        "MedicalHistory",
        back_populates="allergy",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Allergy {self.name}>"


class LaboratoryResult(db.Model):
    __tablename__ = "laboratory_result"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    test_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, index=True)

    patient = db.relationship(
        "Patient",
        back_populates="laboratory_results"
        )

    def __repr__(self):
        return f"<LabResult id={self.id} test={self.test_name}>"


class Prescription(db.Model):
    __tablename__ = "prescription"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)

    patient = db.relationship(
        "Patient",
        back_populates="prescriptions"
        )

    def __repr__(self):
        return f"<Prescription id={self.id} {self.medication_name}>"
