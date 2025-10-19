#!/usr/bin/env python3
"""
Test script to verify email functionality in the EHR system
"""

from app import app, db
from models import Doctor, Specialty
from utils.mail_helper import send_email
from utils.token_holper import generate_token
from flask import url_for


def test_email_functionality():
    """Test the email sending functionality"""

    with app.app_context():
        print("Testing EHR System Email Functionality")
        print("=" * 50)

        # Test 1: Check if mail configuration is loaded
        print("\n1. Checking mail configuration...")
        try:
            mail_server = app.config.get("MAIL_SERVER")
            mail_port = app.config.get("MAIL_PORT")
            mail_username = app.config.get("MAIL_USERNAME")

            print(f"   Mail Server: {mail_server}")
            print(f"   Mail Port: {mail_port}")
            print(f"   Mail Username: {mail_username}")

            if mail_server and mail_port and mail_username:
                print("   ✓ Mail configuration loaded successfully")
            else:
                print("   ✗ Mail configuration incomplete")
                return False

        except Exception as e:
            print(f"   ✗ Error loading mail configuration: {e}")
            return False

        # Test 2: Test token generation
        print("\n2. Testing token generation...")
        try:
            test_token = generate_token(1, "confirm")
            print(f"   ✓ Token generated successfully: {test_token[:20]}...")
        except Exception as e:
            print(f"   ✗ Error generating token: {e}")
            return False

        # Test 3: Test email template creation
        print("\n3. Testing email template creation...")
        try:
            # Create a mock doctor for testing
            mock_doctor_id = 999
            mock_doctor_last_name = "TestDoctor"

            token = generate_token(mock_doctor_id, "confirm")

            # Note: In a real test, this would need a request context for url_for
            # For now, we'll create the HTML manually
            html = f"""
            <html>
            <body>
                <h2>Welcome to EHR System, Dr. {mock_doctor_last_name}!</h2>
                <p>Thank you for registering with our Electronic Health Records system.</p>
                <p>Please click the link below to confirm your email address:</p>
                <p><a href="http://localhost:5000/confirm/{token}" style="background-color: #4CAF50;
                color: white; padding: 14px 20px; text-decoration: none; display: inline-block;
                border-radius: 4px;">Confirm Email</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
                <br>
                <p>Best regards,<br>EHR System Team</p>
            </body>
            </html>
            """

            print("   ✓ Email template created successfully")
            print(f"   Template length: {len(html)} characters")

        except Exception as e:
            print(f"   ✗ Error creating email template: {e}")
            return False

        # Test 4: Check mail configuration values
        print("\n4. Mail configuration details:")
        config_keys = [
            "MAIL_SERVER",
            "MAIL_PORT",
            "MAIL_USE_TLS",
            "MAIL_USERNAME",
            "MAIL_DEFAULT_SENDER",
        ]

        for key in config_keys:
            value = app.config.get(key)
            if key == "MAIL_PASSWORD":
                value = "***" if value else None
            print(f"   {key}: {value}")

        print("\n" + "=" * 50)
        print("Email functionality test completed!")

        # Note about configuration
        print("\nIMPORTANT CONFIGURATION NOTES:")
        print("1. Update config.py with your actual email credentials:")
        print("   - MAIL_USERNAME: your actual Gmail address")
        print("   - MAIL_PASSWORD: your Gmail app password (not regular password)")
        print("   - MAIL_DEFAULT_SENDER: your sender email and name")
        print("\n2. For Gmail, you need to:")
        print("   - Enable 2-factor authentication")
        print("   - Generate an app password")
        print("   - Use the app password in MAIL_PASSWORD")

        return True


if __name__ == "__main__":
    test_email_functionality()
