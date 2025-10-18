# EHR System Email Configuration Guide

## Overview
Your EHR system is already configured to send confirmation emails after user registration. The email functionality includes:

✅ **Email confirmation after registration**
✅ **Password reset emails** 
✅ **Professional HTML email templates**
✅ **Secure token-based verification**

## Current Implementation

The system automatically sends confirmation emails when:
1. A new doctor registers (`/register` endpoint)
2. A doctor requests password reset (`/forgot_password` endpoint)

### Email Flow:
1. **Registration** → Confirmation email → **Email verification** → **Account activated**
2. **Forgot Password** → Reset email → **Password reset** → **New password set**

## Email Configuration Setup

### Step 1: Update config.py
Replace the placeholder values in `config.py`:

```python
# SMTP config (Gmail example)
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "your-actual-email@gmail.com"        # ← Update this
MAIL_PASSWORD = "your-16-digit-app-password"         # ← Update this  
MAIL_DEFAULT_SENDER = ("EHR System", "your-actual-email@gmail.com")  # ← Update this
```

### Step 2: Gmail App Password Setup
1. **Enable 2-Factor Authentication** on your Gmail account
2. Go to **Google Account Settings** → **Security** → **2-Step Verification**
3. Generate an **App Password**:
   - Select "Mail" as the app
   - Select "Other" as the device
   - Name it "EHR System"
   - Copy the 16-digit password
4. Use this 16-digit password in `MAIL_PASSWORD`

### Step 3: Alternative Email Providers

#### For Outlook/Hotmail:
```python
MAIL_SERVER = "smtp-mail.outlook.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
```

#### For Yahoo:
```python
MAIL_SERVER = "smtp.mail.yahoo.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
```

## Testing Email Functionality

Run the test script to verify your configuration:
```bash
python test_email.py
```

## Email Templates

The system includes professional email templates with:
- **Welcome message** with doctor's name
- **Branded EHR System styling**
- **Secure confirmation links** with 24-hour expiration
- **Professional formatting** with buttons and colors

## Security Features

✅ **Token-based verification** (24-hour expiration)
✅ **Secure password hashing**
✅ **SMTP TLS encryption**
✅ **Email confirmation required** before login
✅ **Password reset with secure tokens**

## Troubleshooting

### Common Issues:
1. **"Authentication failed"** → Check app password setup
2. **"SMTP connection failed"** → Check internet connection and MAIL_SERVER
3. **"Email not received"** → Check spam folder, verify email address
4. **"Invalid token"** → Tokens expire after 24 hours

### Debug Mode:
The system includes error handling and will display helpful messages in the web interface.

## Production Considerations

For production deployment:
1. **Use environment variables** for sensitive email credentials
2. **Consider dedicated email service** (SendGrid, Mailgun, AWS SES)
3. **Enable email logging** for monitoring
4. **Set up email queue** for high-volume sending

## Status: ✅ Ready to Use

Your EHR system's email functionality is fully implemented and ready to use once you update the credentials in `config.py`!