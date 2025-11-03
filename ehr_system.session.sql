-- SELECT D.id, D.last_name, S.name
--  FROM doctor AS D
--  JOIN doctor_specialty AS DS ON D.id = DS.doctor_id
--  JOIN specialty AS S ON DS.specialty_id = S.id

-- SELECT * from appointment
SELECT * from laboratory_result


-- SELECT p.first_name, p.last_name, mh.date, mh.notes
-- FROM medical_history  AS mh
-- JOIN patient AS p ON mh.patient_id = p.id
-- JOIN allergy AS a ON mh.allergy_id = a.id

-- ALTER TABLE appointment ADD `notes` TEXT;
-- ALTER TABLE patient CHANGE `patient_avatar_filename` `avatar_filename` VARCHAR(255);

-- SELECT app.id AS appointment_id, p.first_name, p.last_name, d.first_name AS doctor_name, app.date, app.notes 
-- FROM appointment AS app
-- JOIN patient AS p ON app.patient_id = p.id
-- JOIN doctor AS d ON app.doctor_id = d.id

-- INSERT INTO appointment (patient_id, doctor_id, `date`, `status`, `appointment_type`, `notes`, created_at, updated_at)
-- VALUES (4, 2, '2025-10-30 10:00:00', 'SCHEDULED', 'EMERGENCY', 'Patient is experiencing mild symptoms.', NOW(), NOW());