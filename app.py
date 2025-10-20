from flask import Flask, request, redirect, url_for, flash, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import uuid
from config import Config
from models import (
    db,
    Doctor,
    Specialty,
    LaboratoryResult,
    RadiologyImaging,
    Appointment,
    Patient,
    DemographicInfo,
    SocialHistory,
    GenderEnum,
    AppointmentStatusEnum,
    MedicalHistory,
    Allergy,
)
from utils.mail_helper import mail, init_mail, send_email
from utils.token_holper import generate_token, load_token
import re

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
init_mail(app)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/radiology'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'dcm', 'dicom'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(filename):
    """Generate unique filename to prevent conflicts"""
    if filename == '':
        return None
    
    # Get file extension
    file_ext = ''
    if '.' in filename:
        file_ext = '.' + filename.rsplit('.', 1)[1].lower()
    
    # Generate unique filename using UUID
    unique_filename = str(uuid.uuid4()) + file_ext
    return unique_filename


def save_uploaded_file(file, patient_id):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        if filename:
            # Create patient-specific subdirectory
            patient_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'patient_{patient_id}')
            os.makedirs(patient_dir, exist_ok=True)
            
            # Save file
            filepath = os.path.join(patient_dir, filename)
            file.save(filepath)
            return f'patient_{patient_id}/{filename}'
    return None


def delete_image_file(image_filename):
    """Delete image file from filesystem"""
    if image_filename:
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
    return False


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


def send_confirmation_email(doctor):
    """Send email confirmation to new doctor"""
    try:
        token = generate_token(doctor.id, "confirm")
        confirm_url = url_for("confirm_email", token=token, _external=True)

        html = f"""
        <html>
        <body>
            <h2>Welcome to EHR System, Dr. {doctor.last_name}!</h2>
            <p>Thank you for registering with our Electronic Health Records system.</p>
            <p>Please click the link below to confirm your email address:</p>
            <p><a href="{confirm_url}" style="background-color: #4CAF50;
            color: white; padding: 14px 20px; text-decoration: none; display: inline-block;
            border-radius: 4px;">Confirm Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create this account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>EHR System Team</p>
        </body>
        </html>
        """

        send_email(
            subject="Confirm your EHR System account",
            recipients=[doctor.email],
            html=html,
        )
        return True

    except Exception as e:
        print(f"Failed to send confirmation email: {e}")
        return False


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    return redirect(url_for("login_user"))


@app.route("/login", methods=["POST"])
def login_user():
    try:
        # Get form data
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Validation
        if not username_or_email or not password:
            flash("Username/email and password are required.", "error")
            return redirect(url_for("login"))

        # Find user by username or email
        doctor = Doctor.query.filter(
            (Doctor.username == username_or_email)
            | (Doctor.email == username_or_email.lower())
        ).first()

        # Check if user exists
        if not doctor:
            flash("Invalid username/email or password.", "error")
            return redirect(url_for("login"))

        # Check password
        if not check_password_hash(doctor.password, password):
            flash("Invalid username/email or password.", "error")
            return redirect(url_for("login"))

        # Check if email is confirmed
        if not doctor.email_confirmed:
            flash(
                "Please confirm your email address before logging in."
                "Check your email for the confirmation link.",
                "warning",
            )
            return redirect(url_for("login"))

        # Login successful - set up session
        session["doctor_id"] = doctor.id
        session["doctor_name"] = f"Dr. {doctor.last_name}"
        session["logged_in"] = True

        flash(f"Welcome back, Dr. {doctor.last_name}!", "success")
        return redirect(url_for("dashboard"))

    except Exception:
        flash("An error occurred during login. Please try again.", "error")
        return redirect(url_for("login"))


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("forgot_password"))

        doctor = Doctor.query.filter_by(email=email).first()
        if not doctor:
            flash("No account found with that email address.", "error")
            return redirect(url_for("forgot_password"))

        # Generate password reset token
        token = generate_token(doctor.id, "reset_password")
        reset_url = url_for("reset_password", token=token, _external=True)

        html = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi Dr. {doctor.last_name},</p>
            <p>To reset your password, please click the link below:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>EHR System Team</p>
        </body>
        </html>
        """

        send_email(
            subject="Reset your EHR System password",
            recipients=[doctor.email],
            html=html,
        )
        flash("Password reset email sent. Please check your inbox.", "info")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        # Verify token (24 hours expiry)
        doctor_id = load_token(
            token, max_age_seconds=86400, expected_purpose="reset_password"
        )
        doctor = Doctor.query.get(doctor_id)

        if not doctor:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("login"))

        if request.method == "POST":
            new_password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            # Validation
            if not new_password or not confirm_password:
                flash("Both password fields are required.", "error")
                return render_template("reset_password.html")

            if new_password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("reset_password.html")

            # Password strength validation
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                flash(msg, "error")
                return render_template("reset_password.html")

            # Update password
            doctor.password = generate_password_hash(new_password)
            db.session.commit()

            flash("Password reset successfully! You can now log in.", "success")
            return redirect(url_for("login"))

        return render_template("reset_password.html")

    except Exception:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    # Check if user is logged in
    if not session.get("logged_in"):
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")
    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        flash("Doctor not found. Please log in again.", "error")
        return redirect(url_for("logout"))

    try:
        # Get recent lab results for this doctor's patients
        # First check if both tables exist and have the right schema
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        if "laboratory_result" in tables and "patient" in tables:
            # Check if patient table has email column
            patient_columns = [col["name"] for col in inspector.get_columns("patient")]
            if "email" in patient_columns:
                lab_results = (
                    db.session.query(LaboratoryResult, Patient)
                    .join(Patient, LaboratoryResult.patient_id == Patient.id)
                    .filter(Patient.doctor_id == doctor_id)
                    .order_by(LaboratoryResult.date.desc())
                    .limit(10)
                    .all()
                )
            else:
                print("Patient table missing email column - skipping lab results query")
                lab_results = []
        else:
            print(f"Missing tables - available: {tables}")
            lab_results = []
    except Exception as e:
        print(f"Error fetching lab results: {e}")
        lab_results = []

    try:
        # Get upcoming appointments for this doctor
        appointments = (
            Appointment.query.filter_by(doctor_id=doctor_id)
            .order_by(Appointment.date.desc())
            .limit(10)
            .all()
        )
    except Exception as e:
        print(f"Error fetching appointments: {e}")
        appointments = []

    return render_template(
        "dashboard.html",
        lab_results=lab_results,
        appointments=appointments,
        doctor=doctor,
    )


@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    # Check if user is logged in
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            doctor_id = session.get("doctor_id")

            # Get form data
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            age = request.form.get("age", "").strip()
            gender = request.form.get("gender", "").strip()
            date_of_birth = request.form.get("date_of_birth", "").strip()
            phone_number = request.form.get("phone_number", "").strip()
            address = request.form.get("address", "").strip()
            emergency_contact = request.form.get("emergency_contact", "").strip()

            # Validation
            errors = []
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if age and not age.isdigit():
                errors.append("Age must be a number")
            if date_of_birth:
                try:
                    from datetime import datetime

                    datetime.strptime(date_of_birth, "%Y-%m-%d")
                except ValueError:
                    errors.append("Invalid date format")

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("add_patient.html")

            # Create new patient
            patient_gender = None
            if gender:
                patient_gender = GenderEnum(gender)

            new_patient = Patient(
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                age=int(age) if age else None,
                gender=patient_gender,
                date_of_birth=(
                    datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                    if date_of_birth
                    else None
                ),
                doctor_id=doctor_id,
            )

            db.session.add(new_patient)
            db.session.commit()

            # Add demographic info if provided
            if phone_number or address or emergency_contact:
                demographic_info = DemographicInfo(
                    patient_id=new_patient.id,
                    phone_number=phone_number if phone_number else None,
                    address=address if address else None,
                    emergency_contact=emergency_contact if emergency_contact else None,
                )
                db.session.add(demographic_info)

            # Add social history if provided
            smoking_status = (
                "yes" if request.form.get("smoking_status") == "1" else "no"
            )
            alcohol_use = request.form.get("alcohol_use", "").strip()
            drug_use = request.form.get("drug_use", "").strip()
            occupation = request.form.get("occupation", "").strip()

            if smoking_status != "no" or alcohol_use or drug_use or occupation:
                try:
                    # Create social history - smoking_status as string for compatibility
                    social_history = SocialHistory(
                        patient_id=new_patient.id,
                        smoking_status=smoking_status,
                        alcohol_use=alcohol_use if alcohol_use else None,
                        drug_use=drug_use if drug_use else None,
                        occupation=occupation if occupation else None,
                    )
                    db.session.add(social_history)
                except Exception as social_err:
                    print(f"Warning: Could not save social history: {social_err}")
                    # Continue without social history if there's a column issue

            db.session.commit()
            flash(f"Patient {first_name} {last_name} added successfully!", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding patient: {str(e)}", "error")
            return render_template("add_patient.html")

    return render_template("add_patient.html")


@app.route("/schedule_appointment", methods=["GET", "POST"])
def schedule_appointment():
    # Check if user is logged in
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    if request.method == "POST":
        try:
            # Get form data
            patient_id = request.form.get("patient_id", "").strip()
            appointment_date = request.form.get("appointment_date", "").strip()
            appointment_time = request.form.get("appointment_time", "").strip()

            # Validation
            errors = []
            if not patient_id:
                errors.append("Please select a patient")
            if not appointment_date:
                errors.append("Appointment date is required")
            if not appointment_time:
                errors.append("Appointment time is required")

            # Check if patient belongs to this doctor
            if patient_id:
                patient = Patient.query.filter_by(
                    id=patient_id, doctor_id=doctor_id
                ).first()
                if not patient:
                    errors.append("Invalid patient selection")

            if errors:
                for error in errors:
                    flash(error, "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template("schedule_appointment.html", patients=patients)

            # Create appointment datetime
            from datetime import datetime

            appointment_datetime = datetime.strptime(
                f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
            )

            # Check for existing appointment at same time
            existing_appointment = Appointment.query.filter_by(
                doctor_id=doctor_id, date=appointment_datetime
            ).first()

            if existing_appointment:
                flash("You already have an appointment at this date and time.", "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template("schedule_appointment.html", patients=patients)

            # Create new appointment
            new_appointment = Appointment(
                patient_id=int(patient_id),
                doctor_id=doctor_id,
                date=appointment_datetime,
                status=AppointmentStatusEnum.SCHEDULED,
            )

            db.session.add(new_appointment)
            db.session.commit()

            patient = Patient.query.get(patient_id)
            flash(
                f"Appointment scheduled for {patient.first_name} {patient.last_name}!",
                "success",
            )
            flash(
                f'Date and time: {appointment_datetime.strftime("%Y-%m-%d at %H:%M")}',
                "info",
            )
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error scheduling appointment: {str(e)}", "error")
            patients = (
                Patient.query.filter_by(doctor_id=doctor_id)
                .order_by(Patient.last_name)
                .all()
            )
            return render_template("schedule_appointment.html", patients=patients)

    # Get patients for dropdown
    patients = (
        Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.last_name).all()
    )
    # Get pre-selected patient ID from URL parameter
    selected_patient_id = request.args.get("patient_id")
    return render_template(
        "schedule_appointment.html",
        patients=patients,
        selected_patient_id=selected_patient_id,
    )


@app.route("/add_lab_result", methods=["GET", "POST"])
def add_lab_result():
    # Check if user is logged in
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    if request.method == "POST":
        try:
            # Get form data
            patient_id = request.form.get("patient_id", "").strip()
            test_name = request.form.get("test_name", "").strip()
            result = request.form.get("result", "").strip()
            test_date = request.form.get("test_date", "").strip()

            # Validation
            errors = []
            if not patient_id:
                errors.append("Please select a patient")
            if not test_name:
                errors.append("Test name is required")
            if not result:
                errors.append("Result is required")
            if not test_date:
                errors.append("Test date is required")

            # Check if patient belongs to this doctor
            if patient_id:
                patient = Patient.query.filter_by(
                    id=patient_id, doctor_id=doctor_id
                ).first()
                if not patient:
                    errors.append("Invalid patient selection")

            if errors:
                for error in errors:
                    flash(error, "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template("add_lab_result.html", patients=patients)

            # Create test datetime
            try:
                # Try datetime-local format first (YYYY-MM-DDTHH:MM)
                test_datetime = datetime.strptime(test_date, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    # Try date-only format (YYYY-MM-DD)
                    test_datetime = datetime.strptime(test_date, "%Y-%m-%d")
                except ValueError:
                    errors.append("Invalid date format")
                    for error in errors:
                        flash(error, "error")
                    patients = (
                        Patient.query.filter_by(doctor_id=doctor_id)
                        .order_by(Patient.last_name)
                        .all()
                    )
                    return render_template("add_lab_result.html", patients=patients)

            # Create new lab result
            new_lab_result = LaboratoryResult(
                patient_id=int(patient_id),
                test_name=test_name,
                result=result,
                date=test_datetime,
            )

            db.session.add(new_lab_result)
            db.session.commit()

            patient = Patient.query.get(patient_id)
            flash(
                f"Lab result added for {patient.first_name} {patient.last_name}: {test_name}",
                "success",
            )
            return redirect(url_for("dashboard"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding lab result: {str(e)}", "error")
            patients = (
                Patient.query.filter_by(doctor_id=doctor_id)
                .order_by(Patient.last_name)
                .all()
            )
            return render_template("add_lab_result.html", patients=patients)

    # Get patients for dropdown
    patients = (
        Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.last_name).all()
    )
    # Get pre-selected patient ID from URL parameter
    selected_patient_id = request.args.get("patient_id")
    return render_template(
        "add_lab_result.html",
        patients=patients,
        selected_patient_id=selected_patient_id,
    )


@app.route("/patients")
def view_all_patients():
    """Display all patients in a table"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get all patients for this doctor with their demographic info
        patients_query = Patient.query.filter_by(doctor_id=doctor_id).order_by(
            Patient.last_name, Patient.first_name
        )
        patients = patients_query.all()

        # Get patient statistics
        total_patients = len(patients)
        male_patients = sum(1 for p in patients if p.gender == GenderEnum.MALE)
        female_patients = sum(1 for p in patients if p.gender == GenderEnum.FEMALE)
        other_patients = total_patients - male_patients - female_patients

        # Calculate age groups
        current_date = date.today()
        age_groups = {"0-18": 0, "19-35": 0, "36-50": 0, "51-65": 0, "65+": 0}

        for patient in patients:
            if patient.date_of_birth:
                age = (current_date - patient.date_of_birth).days // 365
                if age <= 18:
                    age_groups["0-18"] += 1
                elif age <= 35:
                    age_groups["19-35"] += 1
                elif age <= 50:
                    age_groups["36-50"] += 1
                elif age <= 65:
                    age_groups["51-65"] += 1
                else:
                    age_groups["65+"] += 1

        # Get appointment, lab result, and medical history counts for each patient
        for patient in patients:
            patient.appointment_count = Appointment.query.filter_by(
                patient_id=patient.id
            ).count()
            patient.lab_result_count = LaboratoryResult.query.filter_by(
                patient_id=patient.id
            ).count()
            patient.radiology_result_count = RadiologyImaging.query.filter_by(
                patient_id=patient.id
            ).count()
            patient.medical_history_count = MedicalHistory.query.filter_by(
                patient_id=patient.id
            ).count()

            # Get recent medical histories with allergy information
            patient.recent_medical_histories = (
                db.session.query(MedicalHistory, Allergy)
                .join(Allergy, MedicalHistory.allergy_id == Allergy.id)
                .filter(MedicalHistory.patient_id == patient.id)
                .order_by(MedicalHistory.date.desc())
                .limit(3)
                .all()
            )

        # Calculate patients with medical history
        patients_with_history = sum(1 for p in patients if p.medical_history_count > 0)

        stats = {
            "total_patients": total_patients,
            "male_patients": male_patients,
            "female_patients": female_patients,
            "other_patients": other_patients,
            "age_groups": age_groups,
            "patients_with_history": patients_with_history,
        }

        return render_template("patients.html", patients=patients, stats=stats)

    except Exception as e:
        flash(f"Error loading patients: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/add_medical_history", methods=["GET", "POST"])
def add_medical_history():
    """Add medical history entry for a patient"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    if request.method == "POST":
        try:
            # Get form data
            patient_id = request.form.get("patient_id", "").strip()
            allergy_id = request.form.get("allergy_id", "").strip()
            description = request.form.get("description", "").strip()
            history_date = request.form.get("history_date", "").strip()

            # Validation
            errors = []
            if not patient_id:
                errors.append("Please select a patient")
            if not allergy_id:
                errors.append("Please select an allergy")
            if not description:
                errors.append("Description is required")
            if not history_date:
                errors.append("Date is required")

            # Check if patient belongs to this doctor
            if patient_id:
                patient = Patient.query.filter_by(
                    id=patient_id, doctor_id=doctor_id
                ).first()
                if not patient:
                    errors.append("Invalid patient selection")

            if errors:
                for error in errors:
                    flash(error, "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                allergies = Allergy.query.order_by(Allergy.name).all()
                return render_template(
                    "add_medical_history.html", patients=patients, allergies=allergies
                )

            # Parse date

            history_datetime = datetime.strptime(history_date, "%Y-%m-%d")

            # Create new medical history entry
            new_history = MedicalHistory(
                patient_id=int(patient_id),
                allergy_id=int(allergy_id),
                description=description,
                date=history_datetime,
            )

            db.session.add(new_history)
            db.session.commit()

            patient = Patient.query.get(patient_id)
            allergy = Allergy.query.get(allergy_id)
            flash(
                f"Medical history added for {patient.first_name} {patient.last_name}!",
                "success",
            )
            flash(f"Allergy: {allergy.name}", "info")
            return redirect(url_for("view_all_patients"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding medical history: {str(e)}", "error")
            patients = (
                Patient.query.filter_by(doctor_id=doctor_id)
                .order_by(Patient.last_name)
                .all()
            )
            allergies = Allergy.query.order_by(Allergy.name).all()
            return render_template(
                "add_medical_history.html", patients=patients, allergies=allergies
            )

    # Get patients and allergies for dropdowns
    patients = (
        Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.last_name).all()
    )

    allergies = Allergy.query.order_by(Allergy.name).all()

    # If no allergies exist, create common ones
    if not allergies:
        try:
            common_allergies = [
                (
                    "Penicillin",
                    "Antibiotic allergy - can cause rash, hives, or anaphylaxis",
                ),
                (
                    "Peanuts",
                    "Food allergy - can cause severe reactions, requires avoidance",
                ),
                ("Shellfish", "Food allergy - can cause mild to severe reactions"),
                ("Dust Mites", "Environmental allergy - causes respiratory symptoms"),
                ("Pollen", "Seasonal allergy - causes hay fever symptoms"),
                ("Latex", "Contact allergy - causes skin and systemic reactions"),
                ("Sulfa Drugs", "Medication allergy - can cause skin rashes and fever"),
                (
                    "Aspirin",
                    "Medication allergy - causes respiratory or skin reactions",
                ),
                ("Eggs", "Food allergy - common in children, various symptoms"),
                ("Dairy/Milk", "Food allergy - causes digestive and skin reactions"),
                ("Other", "For allergies not listed above - specify in description"),
            ]

            for name, description in common_allergies:
                allergy = Allergy(name=name, description=description)
                db.session.add(allergy)

            db.session.commit()
            allergies = Allergy.query.order_by(Allergy.name).all()
            flash("Common allergies have been added to the system.", "info")

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating allergies: {str(e)}", "error")
    # Get pre-selected patient ID from URL parameter
    selected_patient_id = request.args.get("patient_id")
    return render_template(
        "add_medical_history.html",
        patients=patients,
        allergies=allergies,
        selected_patient_id=selected_patient_id,
    )


@app.route("/view_lab_results")
def view_lab_results():
    """Display all lab results"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get all lab results for patients of this doctor
        lab_results_query = (
            db.session.query(LaboratoryResult, Patient)
            .join(Patient, LaboratoryResult.patient_id == Patient.id)
            .filter(Patient.doctor_id == doctor_id)
            .order_by(LaboratoryResult.date.desc())
        )

        lab_results = lab_results_query.all()

        # Get statistics
        total_results = len(lab_results)
        recent_results = len(
            [lr for lr, p in lab_results if (datetime.now() - lr.date).days <= 7]
        )

        # Get unique test types
        test_types = set([lr.test_name for lr, p in lab_results])

        stats = {
            "total_results": total_results,
            "recent_results": recent_results,
            "test_types_count": len(test_types),
            "test_types": sorted(list(test_types)),
        }

        return render_template(
            "lab_results.html", lab_results=lab_results, stats=stats, datetime=datetime
        )

    except Exception as e:
        print(f"Debug - Lab results error: {str(e)}")  # Add debug print
        flash(f"Error loading lab results: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/view_appointments")
def view_appointments():
    """Display all appointments"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get all appointments for this doctor
        appointments = (
            Appointment.query.filter_by(doctor_id=doctor_id)
            .join(Patient)
            .order_by(Appointment.date.desc())
            .all()
        )

        # Get statistics
        total_appointments = len(appointments)
        upcoming_appointments = len(
            [a for a in appointments if a.date > datetime.now()]
        )
        completed_appointments = len(
            [a for a in appointments if a.status == AppointmentStatusEnum.COMPLETED]
        )

        # Get appointments by status
        scheduled = len(
            [a for a in appointments if a.status == AppointmentStatusEnum.SCHEDULED]
        )
        cancelled = len(
            [a for a in appointments if a.status == AppointmentStatusEnum.CANCELLED]
        )

        stats = {
            "total_appointments": total_appointments,
            "upcoming_appointments": upcoming_appointments,
            "completed_appointments": completed_appointments,
            "scheduled_appointments": scheduled,
            "cancelled_appointments": cancelled,
        }

        return render_template(
            "appointments.html",
            appointments=appointments,
            stats=stats,
            datetime=datetime,
        )

    except Exception as e:
        flash(f"Error loading appointments: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/view_appointment/<int:appointment_id>")
def view_appointment(appointment_id):
    """View a specific appointment"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get the appointment and ensure it belongs to this doctor
        appointment = (
            Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id)
            .join(Patient)
            .first()
        )

        if not appointment:
            flash("Appointment not found or access denied.", "error")
            return redirect(url_for("dashboard"))

        return render_template(
            "view_appointment.html", appointment=appointment, datetime=datetime
        )

    except Exception as e:
        flash(f"Error loading appointment: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/edit_appointment/<int:appointment_id>", methods=["GET", "POST"])
def edit_appointment(appointment_id):
    """Edit a specific appointment"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get the appointment and ensure it belongs to this doctor
        appointment = (
            Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id)
            .join(Patient)
            .first()
        )

        if not appointment:
            flash("Appointment not found or access denied.", "error")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            # Get form data
            appointment_date = request.form.get("appointment_date", "").strip()
            appointment_time = request.form.get("appointment_time", "").strip()
            status = request.form.get("status", "").strip()
            notes = request.form.get("notes", "").strip()

            # Validation
            errors = []
            if not appointment_date:
                errors.append("Appointment date is required")
            if not appointment_time:
                errors.append("Appointment time is required")
            if not status:
                errors.append("Status is required")

            if errors:
                for error in errors:
                    flash(error, "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template(
                    "edit_appointment.html",
                    appointment=appointment,
                    patients=patients,
                    datetime=datetime,
                )

            # Create new appointment datetime
            appointment_datetime = datetime.strptime(
                f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
            )

            # Check for existing appointment at same time (excluding current appointment)
            existing_appointment = (
                Appointment.query.filter_by(
                    doctor_id=doctor_id, date=appointment_datetime
                )
                .filter(Appointment.id != appointment_id)
                .first()
            )

            if existing_appointment:
                flash(
                    "You already have another appointment at this date and time.",
                    "error",
                )
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template(
                    "edit_appointment.html",
                    appointment=appointment,
                    patients=patients,
                    datetime=datetime,
                )

            # Update appointment
            appointment.date = appointment_datetime
            appointment.status = AppointmentStatusEnum(status)
            appointment.notes = notes if notes else None
            db.session.commit()

            flash(
                f"Appointment updated successfully for "
                f"{appointment.patient.first_name} {appointment.patient.last_name}!",
                "success",
            )
            return redirect(url_for("view_appointments"))

        # GET request - show edit form
        patients = (
            Patient.query.filter_by(doctor_id=doctor_id)
            .order_by(Patient.last_name)
            .all()
        )
        return render_template(
            "edit_appointment.html",
            appointment=appointment,
            patients=patients,
            datetime=datetime,
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error editing appointment: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/delete_appointment/<int:appointment_id>", methods=["POST"])
def delete_appointment(appointment_id):
    """Delete a specific appointment"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get the appointment and ensure it belongs to this doctor
        appointment = (
            Appointment.query.filter_by(id=appointment_id, doctor_id=doctor_id)
            .join(Patient)
            .first()
        )

        if not appointment:
            flash("Appointment not found or access denied.", "error")
            return redirect(url_for("dashboard"))

        # Store patient name for flash message
        patient_name = (
            f"{appointment.patient.first_name} {appointment.patient.last_name}"
        )

        # Delete the appointment
        db.session.delete(appointment)
        db.session.commit()

        flash(
            f"Appointment for {patient_name} has been deleted successfully.", "success"
        )

        # Redirect based on source
        source = request.form.get("source", "")
        if source == "dashboard":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("view_appointments"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting appointment: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/about_us")
def about_us():
    """Display about us page"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    try:
        # Get system statistics
        total_patients = Patient.query.filter_by(doctor_id=doctor_id).count()
        total_appointments = Appointment.query.filter_by(doctor_id=doctor_id).count()
        total_lab_results = (
            db.session.query(LaboratoryResult)
            .join(Patient)
            .filter(Patient.doctor_id == doctor_id)
            .count()
        )
        active_doctors = 1  # Current doctor

        system_stats = {
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "total_lab_results": total_lab_results,
            "active_doctors": active_doctors,
        }

        return render_template(
            "about_us.html", system_stats=system_stats, datetime=datetime
        )

    except Exception as e:
        flash(f"Error loading about page: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    # Clear session
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/doctor_profile")
def doctor_profile():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    
    doctor = Doctor.query.get(session["doctor_id"])
    if not doctor:
        flash("Doctor profile not found.", "error")
        return redirect(url_for("dashboard"))
    
    return render_template("doctor_profile.html", doctor=doctor)


@app.route("/edit_doctor_profile", methods=["GET", "POST"])
def edit_doctor_profile():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    
    doctor = Doctor.query.get(session["doctor_id"])
    if not doctor:
        flash("Doctor profile not found.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        try:
            # Update doctor information
            doctor.first_name = request.form["first_name"]
            doctor.last_name = request.form["last_name"]
            doctor.phone_number = request.form["phone_number"]
            doctor.email = request.form["email"]
            
            # Update session doctor name if last name changed
            session["doctor_name"] = f"Dr. {doctor.last_name}"
            
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("doctor_profile"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "error")
            return render_template("edit_doctor_profile.html", doctor=doctor)
    
    return render_template("edit_doctor_profile.html", doctor=doctor)


@app.route("/register.html")
def register():
    return render_template("register.html")


@app.route("/register_success")
def register_success():
    return render_template("register_success.html")


@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        # Token expires in 24 hours (86400 seconds)
        doctor_id = load_token(token, max_age_seconds=86400, expected_purpose="confirm")

        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash("Invalid confirmation link.", "error")
            return redirect(url_for("login"))

        if doctor.email_confirmed:
            flash("Email already confirmed. Please log in.", "info")
            return redirect(url_for("login"))

        # Confirm the email
        doctor.email_confirmed = True
        from datetime import datetime

        doctor.email_confirmed_at = datetime.utcnow()
        db.session.commit()

        flash("Email confirmed successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    except Exception:
        flash("Invalid or expired confirmation link.", "error")
        return redirect(url_for("login"))


@app.route("/register", methods=["POST"])
def register_doctor():
    try:
        # Get form data
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        phone_number = request.form.get("phone", "").strip()
        specialty_name = request.form.get("speciality", "").strip()

        # Validation
        errors = []

        # Required fields
        if not last_name:
            errors.append("Last name is required")
        if not username:
            errors.append("Username is required")
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")

        # Email format validation
        if email and not validate_email(email):
            errors.append("Invalid email format")

        # Password strength validation
        if password:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)

        # Username validation
        if username and (len(username) < 3 or len(username) > 20):
            errors.append("Username must be between 3 and 20 characters")

        # Check for existing username or email
        if username or email:
            existing_doctor = Doctor.query.filter(
                (Doctor.username == username) | (Doctor.email == email)
            ).first()

            if existing_doctor:
                if existing_doctor.username == username:
                    errors.append("Username already exists")
                if existing_doctor.email == email:
                    errors.append("Email already exists")

        # If there are validation errors, return them
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("register"))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new doctor
        new_doctor = Doctor(
            first_name=first_name if first_name else None,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_password,
            phone_number=phone_number if phone_number else None,
            email_confirmed=False,  # Email not confirmed yet
        )

        # Handle specialty if provided
        if specialty_name:
            specialty = Specialty.query.filter_by(name=specialty_name).first()
            if not specialty:
                specialty = Specialty(name=specialty_name)
                db.session.add(specialty)

            new_doctor.specialties.append(specialty)

        # Add to database
        db.session.add(new_doctor)
        db.session.commit()

        # Send confirmation email
        email_sent = send_confirmation_email(new_doctor)

        if email_sent:
            flash(
                (
                    f"Registration successful! A confirmation email has been sent "
                    f"to {email}. Please check your email to activate your account."
                ),
                "success",
            )
        else:
            flash(
                (
                    "Registration successful! However, we couldn't "
                    "send the confirmation email. Please contact support."
                ),
                "warning",
            )

        return redirect(url_for("register_success"))

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during registration: {str(e)}", "error")
        return redirect(url_for("register"))


@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(
            password, method="sha256"
        )  # Hash the password
        new_doctor = Doctor(username=username, email=email, password=hashed_password)
        db.session.add(new_doctor)
        db.session.commit()
        return "Doctor Added!"
    return """
        <form method="POST">
            Username: <input type="text" name="username"><br>
            Email: <input type="text" name="email"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Add Doctor">
        </form>
    """


# --- Patient Details Route ---


@app.route("/patient/<int:patient_id>")
def view_patient(patient_id):
    """Display detailed info for a single patient"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")
    patient = Patient.query.filter_by(id=patient_id, doctor_id=doctor_id).first()
    if not patient:
        flash("Patient not found or access denied.", "error")
        return redirect(url_for("view_all_patients"))

    # Get related info
    appointments = (
        Appointment.query.filter_by(patient_id=patient.id)
        .order_by(Appointment.date.desc())
        .all()
    )
    lab_results = (
        LaboratoryResult.query.filter_by(patient_id=patient.id)
        .order_by(LaboratoryResult.date.desc())
        .all()
    )
    radiology_imaging = (
        RadiologyImaging.query.filter_by(patient_id=patient.id)
        .order_by(RadiologyImaging.date.desc())
        .all()
    )
    medical_histories = (
        db.session.query(MedicalHistory, Allergy)
        .join(Allergy, MedicalHistory.allergy_id == Allergy.id)
        .filter(MedicalHistory.patient_id == patient.id)
        .order_by(MedicalHistory.date.desc())
        .all()
    )
    return render_template(
        "view_patient.html",
        patient=patient,
        appointments=appointments,
        lab_results=lab_results,
        radiology_imaging=radiology_imaging,
        medical_histories=medical_histories,
    )


@app.route("/edit_patient/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    """Edit patient information"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")
    patient = Patient.query.filter_by(id=patient_id, doctor_id=doctor_id).first()
    if not patient:
        flash("Patient not found or access denied.", "error")
        return redirect(url_for("view_all_patients"))

    if request.method == "POST":
        try:
            # Get form data
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            date_of_birth = request.form.get("date_of_birth", "").strip()
            gender = request.form.get("gender", "").strip()
            phone_number = request.form.get("phone_number", "").strip()
            address = request.form.get("address", "").strip()
            emergency_contact = request.form.get("emergency_contact", "").strip()

            # Validation
            errors = []
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")

            # Parse date
            if date_of_birth:
                try:
                    patient.date_of_birth = datetime.strptime(
                        date_of_birth, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    errors.append("Invalid date format")

            # Validate gender
            if gender:
                if gender not in ["male", "female", "other"]:
                    errors.append("Invalid gender selection")
                else:
                    patient.gender = GenderEnum(gender)

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("edit_patient.html", patient=patient)

            # Update patient
            patient.first_name = first_name
            patient.last_name = last_name
            patient.email = email if email else None

            # Update or create demographic info
            if phone_number or address or emergency_contact:
                if patient.demographic_info:
                    # Update existing demographic info
                    patient.demographic_info.phone_number = (
                        phone_number if phone_number else None
                    )
                    patient.demographic_info.address = address if address else None
                    patient.demographic_info.emergency_contact = (
                        emergency_contact if emergency_contact else None
                    )
                else:
                    # Create new demographic info
                    demographic_info = DemographicInfo(
                        patient_id=patient.id,
                        phone_number=phone_number if phone_number else None,
                        address=address if address else None,
                        emergency_contact=(
                            emergency_contact if emergency_contact else None
                        ),
                    )
                    db.session.add(demographic_info)

            # Update or create social history
            smoking_status = (
                "yes" if request.form.get("smoking_status") == "1" else "no"
            )
            alcohol_use = request.form.get("alcohol_use", "").strip()
            drug_use = request.form.get("drug_use", "").strip()
            occupation = request.form.get("occupation", "").strip()

            # Handle social history
            if patient.social_history:
                # Update existing social history
                patient.social_history.smoking_status = smoking_status
                patient.social_history.alcohol_use = (
                    alcohol_use if alcohol_use else None
                )
                patient.social_history.drug_use = drug_use if drug_use else None
                patient.social_history.occupation = occupation if occupation else None
            else:
                # Create new social history if any field has data
                if smoking_status != "no" or alcohol_use or drug_use or occupation:
                    social_history = SocialHistory(
                        patient_id=patient.id,
                        smoking_status=smoking_status,
                        alcohol_use=alcohol_use if alcohol_use else None,
                        drug_use=drug_use if drug_use else None,
                        occupation=occupation if occupation else None,
                    )
                    db.session.add(social_history)

            db.session.commit()
            flash(f"Patient {first_name} {last_name} updated successfully!", "success")
            return redirect(url_for("view_patient", patient_id=patient.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating patient: {str(e)}", "error")

    return render_template("edit_patient.html", patient=patient)


@app.route("/delete_patient/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    """Delete patient and all related records"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")
    patient = Patient.query.filter_by(id=patient_id, doctor_id=doctor_id).first()
    if not patient:
        flash("Patient not found or access denied.", "error")
        return redirect(url_for("view_all_patients"))

    try:
        patient_name = f"{patient.first_name} {patient.last_name}"

        # Delete related records first to avoid foreign key constraints
        # Delete appointments
        Appointment.query.filter_by(patient_id=patient.id).delete()

        # Delete lab results
        LaboratoryResult.query.filter_by(patient_id=patient.id).delete()

        # Delete medical history
        MedicalHistory.query.filter_by(patient_id=patient.id).delete()

        # Delete patient
        db.session.delete(patient)
        db.session.commit()

        flash(
            f"Patient {patient_name} and all related records deleted successfully!",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting patient: {str(e)}", "error")

    return redirect(url_for("view_all_patients"))


@app.route("/edit_lab_result/<int:lab_result_id>", methods=["GET", "POST"])
def edit_lab_result(lab_result_id):
    """Edit lab result information"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    # Get the lab result and verify access
    lab_result = (
        db.session.query(LaboratoryResult)
        .join(Patient)
        .filter(LaboratoryResult.id == lab_result_id)
        .filter(Patient.doctor_id == doctor_id)
        .first()
    )

    if not lab_result:
        flash("Lab result not found or access denied.", "error")
        return redirect(url_for("view_lab_results"))

    if request.method == "POST":
        try:
            # Get form data
            test_name = request.form.get("test_name", "").strip()
            result = request.form.get("result", "").strip()
            date_str = request.form.get("date", "").strip()

            # Validation
            errors = []
            if not test_name:
                errors.append("Test name is required")
            if not result:
                errors.append("Result is required")
            if not date_str:
                errors.append("Date is required")

            # Parse date
            if date_str:
                try:
                    test_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    errors.append("Invalid date format")

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("edit_lab_result.html", lab_result=lab_result)

            # Update lab result
            lab_result.test_name = test_name
            lab_result.result = result
            lab_result.date = test_date

            db.session.commit()
            patient_name = (
                f"{lab_result.patient.first_name} {lab_result.patient.last_name}"
            )
            flash(f"Lab result for {patient_name} updated successfully!", "success")
            return redirect(url_for("view_lab_results"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating lab result: {str(e)}", "error")

    return render_template("edit_lab_result.html", lab_result=lab_result)


@app.route("/delete_lab_result/<int:lab_result_id>", methods=["POST"])
def delete_lab_result(lab_result_id):
    """Delete lab result"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    # Get the lab result and verify access
    lab_result = (
        db.session.query(LaboratoryResult)
        .join(Patient)
        .filter(LaboratoryResult.id == lab_result_id)
        .filter(Patient.doctor_id == doctor_id)
        .first()
    )

    if not lab_result:
        flash("Lab result not found or access denied.", "error")
        return redirect(url_for("view_lab_results"))

    try:
        patient_name = f"{lab_result.patient.first_name} {lab_result.patient.last_name}"
        test_name = lab_result.test_name

        db.session.delete(lab_result)
        db.session.commit()

        flash(
            f"Lab result ({test_name}) for {patient_name} deleted successfully!",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting lab result: {str(e)}", "error")

    return redirect(url_for("view_lab_results"))


# ===== RADIOLOGY IMAGING ROUTES =====

@app.route("/add_radiology_imaging", methods=["GET", "POST"])
def add_radiology_imaging():
    """Add new radiology imaging record"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    if request.method == "POST":
        try:
            # Get form data
            patient_id = request.form.get("patient_id", "").strip()
            imaging_name = request.form.get("imaging_name", "").strip()
            imaging_date = request.form.get("imaging_date", "").strip()

            # Validation
            errors = []
            if not patient_id:
                errors.append("Please select a patient")
            if not imaging_name:
                errors.append("Imaging name is required")
            if not imaging_date:
                errors.append("Imaging date is required")
            
            # Handle file upload
            image_file = request.files.get('image_file')
            if image_file and image_file.filename != '':
                if not allowed_file(image_file.filename):
                    errors.append("Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF, BMP, TIFF, DCM, DICOM")

            # Check if patient belongs to this doctor
            if patient_id:
                patient = Patient.query.filter_by(
                    id=patient_id, doctor_id=doctor_id
                ).first()
                if not patient:
                    errors.append("Invalid patient selection")

            if errors:
                for error in errors:
                    flash(error, "error")
                patients = (
                    Patient.query.filter_by(doctor_id=doctor_id)
                    .order_by(Patient.last_name)
                    .all()
                )
                return render_template("add_radiology_imaging.html", patients=patients)

            # Create imaging datetime
            try:
                # Try datetime-local format first (YYYY-MM-DDTHH:MM)
                imaging_datetime = datetime.strptime(imaging_date, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    # Try date-only format (YYYY-MM-DD)
                    imaging_datetime = datetime.strptime(imaging_date, "%Y-%m-%d")
                except ValueError:
                    errors.append("Invalid date format")
                    for error in errors:
                        flash(error, "error")
                    patients = (
                        Patient.query.filter_by(doctor_id=doctor_id)
                        .order_by(Patient.last_name)
                        .all()
                    )
                    return render_template("add_radiology_imaging.html", patients=patients)

            # Handle file upload if present
            image_filename = None
            if image_file and image_file.filename != '':
                image_filename = save_uploaded_file(image_file, int(patient_id))
                if not image_filename:
                    errors.append("Failed to save uploaded image")
                    for error in errors:
                        flash(error, "error")
                    patients = (
                        Patient.query.filter_by(doctor_id=doctor_id)
                        .order_by(Patient.last_name)
                        .all()
                    )
                    return render_template("add_radiology_imaging.html", patients=patients)

            # Create new radiology imaging record
            new_imaging = RadiologyImaging(
                patient_id=int(patient_id),
                name=imaging_name,
                date=imaging_datetime,
                image_filename=image_filename,
            )

            db.session.add(new_imaging)
            db.session.commit()

            patient = Patient.query.get(patient_id)
            flash(
                f"Radiology imaging added for {patient.first_name} {patient.last_name}: {imaging_name}",
                "success",
            )
            return redirect(url_for("view_radiology_imaging"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding radiology imaging: {str(e)}", "error")

    # GET request - show form
    patients = (
        Patient.query.filter_by(doctor_id=doctor_id).order_by(Patient.last_name).all()
    )
    selected_patient_id = request.args.get("patient_id", "")
    return render_template(
            "add_radiology_imaging.html",
            patients=patients,
            selected_patient_id=selected_patient_id
        )


@app.route("/view_radiology_imaging")
def view_radiology_imaging():
    """View all radiology imaging records"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    # Get search parameters
    search_patient = request.args.get("search_patient", "").strip()
    search_imaging = request.args.get("search_imaging", "").strip()

    # Build query
    query = (
        db.session.query(RadiologyImaging)
        .join(Patient)
        .filter(Patient.doctor_id == doctor_id)
    )

    # Apply filters
    if search_patient:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f"%{search_patient}%"),
                Patient.last_name.ilike(f"%{search_patient}%"),
            )
        )

    if search_imaging:
        query = query.filter(RadiologyImaging.name.ilike(f"%{search_imaging}%"))

    # Execute query and order results
    radiology_imaging = query.order_by(RadiologyImaging.date.desc()).all()

    return render_template(
        "view_radiology_imaging.html",
        radiology_imaging=radiology_imaging,
        search_patient=search_patient,
        search_imaging=search_imaging,
    )


@app.route("/edit_radiology_imaging/<int:imaging_id>", methods=["GET", "POST"])
def edit_radiology_imaging(imaging_id):
    """Edit radiology imaging record"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    # Get the imaging record and verify access
    imaging = (
        db.session.query(RadiologyImaging)
        .join(Patient)
        .filter(RadiologyImaging.id == imaging_id)
        .filter(Patient.doctor_id == doctor_id)
        .first()
    )

    if not imaging:
        flash("Radiology imaging record not found or access denied.", "error")
        return redirect(url_for("view_radiology_imaging"))

    if request.method == "POST":
        try:
            # Get form data
            imaging_name = request.form.get("imaging_name", "").strip()
            imaging_date = request.form.get("imaging_date", "").strip()

            # Validation
            errors = []
            if not imaging_name:
                errors.append("Imaging name is required")
            if not imaging_date:
                errors.append("Imaging date is required")
            
            # Handle file upload
            image_file = request.files.get('image_file')
            if image_file and image_file.filename != '':
                if not allowed_file(image_file.filename):
                    errors.append("Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF, BMP, TIFF, DCM, DICOM")

            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("edit_radiology_imaging.html", imaging=imaging)

            # Parse date
            try:
                # Try datetime-local format first (YYYY-MM-DDTHH:MM)
                imaging_datetime = datetime.strptime(imaging_date, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    # Try date-only format (YYYY-MM-DD)
                    imaging_datetime = datetime.strptime(imaging_date, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid date format", "error")
                    return render_template("edit_radiology_imaging.html", imaging=imaging)

            # Handle image replacement if new file uploaded
            if image_file and image_file.filename != '':
                # Save new image
                new_image_filename = save_uploaded_file(image_file, imaging.patient_id)
                if new_image_filename:
                    # Delete old image if it exists
                    if imaging.image_filename:
                        delete_image_file(imaging.image_filename)
                    # Update with new image filename
                    imaging.image_filename = new_image_filename
                else:
                    flash("Failed to save uploaded image", "error")
                    return render_template("edit_radiology_imaging.html", imaging=imaging)

            # Update the imaging record
            imaging.name = imaging_name
            imaging.date = imaging_datetime

            db.session.commit()

            flash(
                f"Radiology imaging updated: {imaging_name}",
                "success",
            )
            return redirect(url_for("view_radiology_imaging"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating radiology imaging: {str(e)}", "error")

    return render_template("edit_radiology_imaging.html", imaging=imaging)


@app.route("/delete_radiology_imaging/<int:imaging_id>", methods=["POST"])
def delete_radiology_imaging(imaging_id):
    """Delete radiology imaging record"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")

    # Get the imaging record and verify access
    imaging = (
        db.session.query(RadiologyImaging)
        .join(Patient)
        .filter(RadiologyImaging.id == imaging_id)
        .filter(Patient.doctor_id == doctor_id)
        .first()
    )

    if not imaging:
        flash("Radiology imaging record not found or access denied.", "error")
        return redirect(url_for("view_radiology_imaging"))

    try:
        patient_name = f"{imaging.patient.first_name} {imaging.patient.last_name}"
        imaging_name = imaging.name
        image_filename = imaging.image_filename

        db.session.delete(imaging)
        db.session.commit()

        # Delete associated image file if it exists
        if image_filename:
            delete_image_file(image_filename)

        flash(
            f"Radiology imaging ({imaging_name}) for {patient_name} deleted successfully!",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting radiology imaging: {str(e)}", "error")

    return redirect(url_for("view_radiology_imaging"))


@app.route("/radiology_image/<path:filename>")
def radiology_image(filename):
    """Serve radiology images securely"""
    if not session.get("logged_in"):
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    doctor_id = session.get("doctor_id")
    
    # Extract patient ID from filename path (format: patient_X/filename.ext)
    try:
        if '/' in filename:
            patient_folder, image_name = filename.split('/', 1)
            patient_id = int(patient_folder.replace('patient_', ''))
            
            # Verify that this patient belongs to the logged-in doctor
            patient = Patient.query.filter_by(id=patient_id, doctor_id=doctor_id).first()
            if not patient:
                flash("Access denied to this image.", "error")
                return redirect(url_for("view_radiology_imaging"))
                
            # Serve the file
            from flask import send_from_directory
            return send_from_directory(
                os.path.join(app.config['UPLOAD_FOLDER'], patient_folder), 
                image_name
            )
        else:
            flash("Invalid image path.", "error")
            return redirect(url_for("view_radiology_imaging"))
            
    except (ValueError, IndexError):
        flash("Invalid image path.", "error")
        return redirect(url_for("view_radiology_imaging"))


if __name__ == "__main__":
    app.run(debug=True)
