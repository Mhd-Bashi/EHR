# VitalTrack EHR System Report

## 1. Introduction
The **VitalTrack EHR System** is a web-based electronic health record platform designed for small clinical practices and individual physicians. It centralizes core patient data domains: demographics, appointments, laboratory diagnostics, radiology imaging metadata and files, medical histories including allergies, and clinician identity management. 

Electronic Health Records streamline care coordination, reduce transcription errors, and preserve longitudinal patient context. This system focuses on providing a clean foundation with secure access, structured clinical data entry, and extensibility for future modules (e.g., prescriptions, vitals, interoperability standards).

### Objectives
- Provide a maintainable, modular codebase using Flask + SQLAlchemy.
- Enforce authentication, email verification, and secure password recovery.
- Support physician-centric workflow: register → confirm → manage patient panel → document encounters/results.
- Enable radiology file storage with controlled access per patient.
- Lay groundwork for future expansions (API, decision support, FHIR integration).

### Development Approach
Incremental layering: authentication → patient master data → appointments → laboratory results → imaging uploads → medical history (allergy normalization) → profile maintenance. Emphasis on clarity of models, predictable enumerations, and reusability of route logic.

## 2. Website Design Overview
The UI uses server-rendered Jinja2 templates with a shared base layout. Navigation prioritizes the most frequently used clinical tasks. Styling is handled via CSS in `static/styles/` with specialized sheets for authentication flows.

### Navigation Structure
- Dashboard
- Patients
- Appointments
- Lab Results
- Radiology Imaging
- Medical History (via add forms & patient aggregation)
- Profile / Account
- Auth flows (Login, Register, Forgot / Reset Password)

### Design Principles
- Simplicity: Minimized input friction and clear grouping.
- Consistency: Shared flash message handling, form field naming patterns.
- Safety: Access gated by confirmed email + session state.
- Scalability: Enum-driven categorical data (appointment types, lab statuses, genders).
- Visibility: Dashboard summarization of recent diagnostics and appointments.

### Representative Template Roles
| Template | Purpose |
|----------|---------|
| `login.html` | Access control entry point |
| `dashboard.html` | Aggregated operational snapshot |
| `patients.html` | Patient list + statistics |
| `view_patient.html` | Longitudinal patient overview |
| `appointments.html` | Scheduling oversight |
| `lab_results.html` | Laboratory chronology |
| `view_radiology_imaging.html` | Imaging records listing & query |
| `doctor_profile.html` | Physician identity display |
| `register.html` / `register_success.html` | Onboarding flows |
| `forgot_password.html` / `reset_password.html` | Credential recovery |

## 3. Technical Architecture

### 3.1 Stack Components
- **Framework:** Flask (routes, session management, templating)
- **ORM:** SQLAlchemy (+ Flask-Migrate/Alembic migrations in `migrations/`)
- **Database:** Configurable via `SQLALCHEMY_DATABASE_URI` (SQLite/PostgreSQL/etc.)
- **Mail:** `flask_mail` for transactional notifications (confirmation, reset)
- **Security:** Werkzeug hashing, itsdangerous timed tokens, session cookies, enumerated statuses
- **Static & Uploads:** CSS + per-patient imaging under `static/uploads/radiology/patient_{id}`
- **Config:** Environment-driven in `config.py`

### 3.2 Module Responsibilities
| Module/File | Responsibility |
|-------------|---------------|
| `app.py` | Route definitions, validators, business logic orchestration |
| `models.py` | Data schema, relationships, enums, constraints |
| `config.py` | Centralized configuration (DB, secrets, mail) |
| `utils/mail_helper.py` | Mail initialization & sending wrapper |
| `utils/token_holper.py` | (Typo) Token generation/validation for confirm & reset |
| `migrations/` | Schema evolution scripts |
| `static/` | Styling and uploaded artifact storage |
| `templates/` | Presentation layer |

### 3.3 Data Model & Relationships
- **Doctor** ↔ **Specialty**: Many-to-many via `doctor_specialty`.
- **Doctor** 1—M **Patient**, **Appointment**.
- **Patient** 1—1 **DemographicInfo**, 1—1 **SocialHistory**.
- **Patient** 1—M **LaboratoryResult**, **RadiologyImaging**, **MedicalHistory**, **Appointment**, **Prescription**.
- **MedicalHistory** M—1 **Allergy** (and transitive patient–allergy view).

Enumerations: `GenderEnum`, `AppointmentStatusEnum`, `AppointmentTypeEnum`, `LabResultStatusEnum` enforce domain vocabulary.

### 3.4 Key Behaviors
- Unique appointment constraint per doctor/time slot.
- Seeding of common allergies when absent.
- Secure radiology file lifecycle (save, update with deletion, secure serve after ownership check).
- Token purpose verification ("confirm" vs "reset_password").

### 3.5 Security Considerations (Implemented & Recommended)
Implemented: Password hashing, email confirmation gate, timed tokens (24h), owner-scoped queries, secure image route.
Recommended: CSRF protection, RBAC expansion, audit logging, XSS sanitization, external object storage, HTTPS enforcement, rate limiting.

### 3.6 Extensibility
Future additions: Prescription management UI, vitals tracking, interoperability (FHIR), portal roles (patient, admin), analytics dashboards, background task queue for heavy operations.

## 4. Feature Walkthrough (User Manual Style)
Below: Each feature with workflow plus a textual "snapshot" description.

### 4.1 Authentication & Access
**Login** (`/` GET, `/login` POST)
- Input: username/email + password.
- Failure: Generic message to avoid enumeration.
- Snapshot: Centered panel, brand heading, links to Register / Forgot Password.

**Registration** (`/register` POST)
- Validates uniqueness, email format, password strength (length, upper, lower, digit, special).
- On success: Doctor created, specialty optionally linked, confirmation mail dispatched.
- Snapshot: Multi-step styled form; success leads to confirmation instructions.

**Email Confirmation** (`/confirm/<token>`)
- Validates token purpose & expiry → sets `email_confirmed`.
- Snapshot: Flash banner: "Email confirmed successfully!".

**Forgot / Reset Password**
- Forgot: Collects email, generates reset token, dispatches HTML email.
- Reset: Token validated, new password complexity enforced.
- Snapshot: Simple single-field request screen; reset form with two password boxes.

**Doctor Profile** (`/doctor_profile`, edit via `/edit_doctor_profile`)
- View/update personal and contact details.
- Snapshot: Profile card (name, email, phone, specialties) with Edit button.

### 4.2 Dashboard (`/dashboard`)
- Shows: Recent Laboratory Results (<=10), Upcoming Appointments (<=10), contextual greeting (Dr. <LastName>).
- Snapshot: Two stacked tables or cards with date descending ordering.

### 4.3 Patient Management
**List Patients** (`/patients`)
- Displays counts per patient: appointments, labs, imaging, medical history.
- Statistics: Gender distribution, age groups, count with histories.
- Snapshot: Table + summary metrics ribbon.

**Add Patient** (`/add_patient`)
- Includes demographic & social history (if provided); validates formats.
- Snapshot: Sectioned form (Identity | Contact | Social History).

**View Patient** (`/patient/<id>`)
- Aggregated longitudinal data: appointments, labs, imaging, histories with allergy names.
- Snapshot: Patient header + collapsible or sequential sections.

**Edit Patient** (`/edit_patient/<id>`)
- Update identity, demographic, social fields.
- Snapshot: Pre-filled form mirroring Add.

**Delete Patient** (`/delete_patient/<id>` POST)
- Cascades dependent records (appointments, labs, medical histories, imaging metadata).
- Snapshot: Confirmation message; irreversible warning recommended (future improvement).

### 4.4 Appointments
**View All** (`/view_appointments`)
- Metrics: Total, Upcoming, Completed, Scheduled, Cancelled, No-show.
- Snapshot: List with color-coded status badges.

**Schedule** (`/schedule_appointment`)
- Prevents overlapping slot for same doctor.
- Snapshot: Patient dropdown + date/time pickers + type select.

**View Single** (`/view_appointment/<id>`)
- Snapshot: Details card with status & notes.

**Edit** (`/edit_appointment/<id>`)
- Conflict detection on updated datetime.
- Snapshot: Form with status and type dropdowns.

**Delete** (`/delete_appointment/<id>` POST)
- Redirect path adapts to originating context.
- Snapshot: Flash confirming removal.

### 4.5 Laboratory Results
**List** (`/view_lab_results`)
- Joins patient; shows test name, date, result, status, reference range.
- Stats: Total, recent (≤7 days), unique test types.
- Snapshot: Table with status chips (e.g., NORMAL / CRITICAL highlight).

**Add / Edit** (`/add_lab_result`, `/edit_lab_result/<id>`)
- Accepts date or datetime-local; validates required fields.
- Snapshot: Form with optional fields (unit, reference range, notes).

**Delete** (`/delete_lab_result/<id>`)
- Snapshot: Flash indicating test + patient removed.

### 4.6 Radiology Imaging
**Add** (`/add_radiology_imaging`)
- Validates file extension; unique UUID naming; patient folder segregation.
- Snapshot: File chooser + allowed formats helper text.

**List / Search** (`/view_radiology_imaging`)
- Filters by patient name or imaging name substring.
- Snapshot: Search inputs above descending list.

**Edit** (`/edit_radiology_imaging/<id>`)
- Supports file replacement; deletes old file.
- Snapshot: Current filename label + optional new upload field.

**Delete** (`/delete_radiology_imaging/<id>`)
- Removes DB row + physical file.
- Snapshot: Success flash referencing patient & imaging name.

**Serve Image** (`/radiology_image/<path>`) 
- Ownership check before streaming; mitigates direct path exploitation.
- Snapshot: Image inline or downloadable.

### 4.7 Medical History & Allergies
**Add History** (`/add_medical_history`)
- Seeds allergies if table empty (common set) then provides dropdown.
- Snapshot: Allergy dropdown + date + free-text description.

**Patient View Integration**
- Histories rendered with associated allergy names ordered by date.
- Snapshot: Chronological list labeled (Allergy: Description — Date).

### 4.8 Prescriptions (Model Present)
- Model exists; UI/routes not implemented yet (expansion opportunity).

### 4.9 Flash Messaging & Validation
- Uniform usage of categories: success, error, warning, info.
- Snapshot: Top-of-page colored banners after redirects.

## 5. Data Integrity & Constraints
- Appointment uniqueness per doctor/time prevents double booking.
- Cascading deletes maintain referential cleanliness.
- Enums constrain domain states preventing inconsistent status strings.
- Timestamps enable audit extension (future: indexing + diff logging).

## 6. Performance & Scaling Considerations
| Aspect | Current | Potential Enhancement |
|--------|---------|------------------------|
| Query Volume | Small practice scale | Pagination, caching common counts |
| File Storage | Local FS | Object storage (S3/Azure Blob) + CDN |
| Email | Synchronous send | Async queue (Celery/RQ) |
| Security | Session + basic checks | RBAC, CSRF, OAuth2/FHIR SMART |
| Observability | Minimal | Structured logging, metrics (Prometheus) |

## 7. Security Summary
Implemented: Hashed passwords, token expiry, ownership checks, minimal surface exposure.
Missing (Recommended): CSRF, brute-force throttling, secure headers (CSP, HSTS), password rotation policy, audit trails, encryption at rest (DB-level, file-level if PHI).

## 8. Roadmap Highlights
1. Implement prescriptions UI & workflow.
2. Add vitals and graphing trends.
3. Introduce paging + search indexing.
4. Expose REST/FHIR API.
5. Add patient portal role with limited access.
6. Deploy with production WSGI & containerization.
7. Integrate object storage & signed URL access.
8. Add background job queue for email & reports.
9. Implement full audit + immutable event log.
10. Integrate decision support (allergy/drug alerts).

## 9. Appendix
### 9.1 Environment Variables
```
SQLALCHEMY_DATABASE_URI=...
SECRET_KEY=...
SECURITY_PASSWORD_SALT=...
MAIL_SERVER=...
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=...
```

### 9.2 Password Policy (Enforced)
- ≥ 8 characters
- ≥ 1 uppercase
- ≥ 1 lowercase
- ≥ 1 digit
- ≥ 1 special character

### 9.3 Allowed Imaging File Types
`png, jpg, jpeg, gif, bmp, tiff, dcm, dicom` (10MB limit)

### 9.4 Core Enums
```
Gender: male | female | other
AppointmentStatus: scheduled | completed | cancelled | no_show
AppointmentType: consultation | follow_up | emergency | check_up | surgery | procedure
LabResultStatus: normal | abnormal | high | low | critical | pending
```

## 10. Conclusion
The VitalTrack EHR System provides a robust foundational layer for structured clinical data management with secure authentication flows and modular clinical domains. Its clear data model, enumerated states, and consistent route patterns position it well for future scaling—adding interoperability, richer analytics, and multi-role support. Strategic enhancements around security hardening, auditability, and performance will advance it from a functional prototype toward production-grade EHR capability.

---
*Generated documentation based on current repository code structure and inferred behaviors.*
