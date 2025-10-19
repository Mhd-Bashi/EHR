# Database Migration Instructions - UPDATED

## Issue Fixed
The error was caused by SQLAlchemy trying to access the `smoking_units` column that doesn't exist in the database yet.

## ✅ Immediate Fix Applied
The code has been temporarily updated to work with the existing database structure:

1. **Model Updated**: Commented out `smoking_units` column in `models.py`
2. **Forms Updated**: Temporarily hidden the smoking units input field
3. **Backend Updated**: Removed references to the non-existent column
4. **Templates Updated**: Fixed smoking_status handling for string values

## Current Status
The application should now work without errors. The social history feature is functional with these fields:
- ✅ Smoking Status (checkbox - stored as "yes"/"no" string)
- ✅ Alcohol Use (dropdown)
- ✅ Drug Use (dropdown) 
- ✅ Occupation (text field)

## Future Enhancement: Add Smoking Units (Optional)

When you're ready to add the smoking amount tracking feature, run this SQL:

```sql
-- Add the smoking units column
ALTER TABLE social_history ADD COLUMN smoking_units VARCHAR(50);

-- Convert smoking_status to boolean (optional)
UPDATE social_history 
SET smoking_status = CASE 
    WHEN smoking_status IN ('yes', 'true', '1') THEN 1
    ELSE 0
END;

ALTER TABLE social_history MODIFY COLUMN smoking_status TINYINT(1) DEFAULT 0;
```

Then uncomment the `smoking_units` field in `models.py` and update the templates.

## ✅ Ready to Use
The application is now functional with social history features! No database migration required for basic functionality.