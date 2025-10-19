-- SQL Migration for social_history table
-- Add smoking_units column and modify smoking_status to TINYINT(1)

-- Add the missing column
ALTER TABLE social_history ADD COLUMN smoking_units VARCHAR(50);

-- Update existing smoking_status data to boolean values (0 or 1)
-- Convert string 'true', 'yes', '1', 'smoker', 'smoking' to 1, everything else to 0
UPDATE social_history 
SET smoking_status = CASE 
    WHEN LOWER(smoking_status) IN ('true', 'yes', '1', 'smoker', 'smoking') THEN 1
    WHEN smoking_status IS NULL OR smoking_status = '' THEN 0
    ELSE 0
END;

-- Modify the column type to TINYINT(1) for proper boolean storage
ALTER TABLE social_history MODIFY COLUMN smoking_status TINYINT(1) DEFAULT 0;