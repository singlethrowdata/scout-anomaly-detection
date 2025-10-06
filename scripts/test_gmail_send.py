#!/usr/bin/env python3
"""
SCOUT Gmail API Test Script
Tests sending HTML email via Gmail API with service account
[R9]: Validate Google Workspace email delivery
"""

import os
import sys
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ ERROR: Google API libraries not installed")
    print("\nInstall with:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

class GmailAPITester:
    """Test Gmail API connectivity and email sending"""

    def __init__(self, service_account_file: str = None):
        """
        Initialize Gmail API client

        Args:
            service_account_file: Path to service account JSON
        """
        print("🔧 SCOUT Gmail API Test\n" + "=" * 60)

        # Find service account file
        self.service_account_file = service_account_file

        if not self.service_account_file:
            # Check common locations
            possible_paths = [
                os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
                'credentials/service-account.json',
                '../credentials/service-account.json',
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    self.service_account_file = path
                    break

        if not self.service_account_file:
            print("❌ ERROR: Service account file not found")
            print("\nPlease provide service account JSON file path:")
            print("  1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            print("  2. Place file at credentials/service-account.json")
            print("  3. Pass file path as argument")
            sys.exit(1)

        print(f"✅ Service account file: {self.service_account_file}\n")

        # Create credentials
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=[
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ]
            )

            # For service accounts, we need to impersonate a user
            # Check if there's a subject (user email) in the credentials
            service_account_email = self.credentials.service_account_email
            print(f"📧 Service Account: {service_account_email}")

            # Note: Service accounts need domain-wide delegation to send emails
            print("\n⚠️  IMPORTANT: Service account needs domain-wide delegation")
            print("   Enable in Google Workspace Admin > Security > API Controls")
            print("   Scopes required:")
            print("   - https://www.googleapis.com/auth/gmail.send")
            print("   - https://www.googleapis.com/auth/gmail.readonly")

        except Exception as e:
            print(f"❌ ERROR: Failed to load service account credentials")
            print(f"   {str(e)}")
            sys.exit(1)

    def test_authentication(self, user_email: str):
        """
        Test Gmail API authentication

        Args:
            user_email: Email address to impersonate (must be in your domain)
        """
        print(f"\n🔐 Testing authentication as: {user_email}")

        try:
            # Create delegated credentials for the user
            delegated_credentials = self.credentials.with_subject(user_email)

            # Build Gmail service
            service = build('gmail', 'v1', credentials=delegated_credentials)

            # Test by getting user profile
            profile = service.users().getProfile(userId='me').execute()

            print(f"✅ Authentication successful!")
            print(f"   Email: {profile.get('emailAddress')}")
            print(f"   Messages: {profile.get('messagesTotal', 0)}")

            return service

        except HttpError as error:
            print(f"❌ Authentication failed: {error}")
            print("\n💡 Troubleshooting:")
            print("   1. Verify domain-wide delegation is enabled")
            print("   2. Check that user email is in your Google Workspace domain")
            print("   3. Verify service account has Gmail API access")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None

    def send_test_email(self, service, to_email: str, subject: str = "SCOUT Test Email"):
        """
        Send a test HTML email

        Args:
            service: Gmail API service object
            to_email: Recipient email address
            subject: Email subject line
        """
        print(f"\n📤 Sending test email to: {to_email}")

        try:
            # Create HTML message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject

            # Plain text version
            text_content = """
SCOUT Test Email

This is a test email from the SCOUT anomaly detection system.

If you received this, Gmail API integration is working correctly!

---
SCOUT - Statistical Client Observation & Unified Tracking
"""

            # HTML version
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #666;
            font-size: 12px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SCOUT Test Email</h1>
        <p>Gmail API Integration Test</p>
    </div>

    <div class="content">
        <h2>🎉 Success!</h2>
        <p>This is a test email from the SCOUT anomaly detection system.</p>

        <div class="success">
            <strong>✅ Gmail API Integration Working</strong><br>
            If you received this email, the Gmail API is properly configured and SCOUT can send automated alerts.
        </div>

        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Configure recipient list for weekly alerts</li>
            <li>Set up Cloud Scheduler for Monday morning delivery</li>
            <li>Test with actual anomaly detection data</li>
        </ul>
    </div>

    <div class="footer">
        <p><strong>SCOUT</strong> - Statistical Client Observation & Unified Tracking</p>
        <p>Automated GA4 Anomaly Detection System</p>
    </div>
</body>
</html>
"""

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            message.attach(part1)
            message.attach(part2)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send email
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            print(f"✅ Email sent successfully!")
            print(f"   Message ID: {send_message.get('id')}")
            print(f"   Thread ID: {send_message.get('threadId')}")

            return True

        except HttpError as error:
            print(f"❌ Failed to send email: {error}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False

def main():
    """Main test execution"""

    # Get user inputs
    print("SCOUT Gmail API Test")
    print("=" * 60)
    print("\nThis script tests Gmail API integration for sending alerts.\n")

    # Get sender email (user to impersonate)
    sender_email = input("Enter sender email (your Google Workspace email): ").strip()
    if not sender_email:
        print("❌ Sender email is required")
        sys.exit(1)

    # Get recipient email
    recipient_email = input("Enter recipient email (where to send test): ").strip()
    if not recipient_email:
        recipient_email = sender_email  # Send to self

    # Initialize tester
    tester = GmailAPITester()

    # Test authentication
    service = tester.test_authentication(sender_email)

    if not service:
        print("\n❌ Authentication failed. Cannot proceed with email test.")
        sys.exit(1)

    # Ask to send test email
    print("\n" + "=" * 60)
    send_test = input(f"\nSend test email to {recipient_email}? (yes/no): ").strip().lower()

    if send_test in ['yes', 'y']:
        success = tester.send_test_email(service, recipient_email)

        if success:
            print("\n" + "=" * 60)
            print("✅ GMAIL API TEST COMPLETE")
            print("=" * 60)
            print("\nGmail API is ready for SCOUT alerts!")
            print("Next: Configure weekly alert schedule")
        else:
            print("\n❌ Email sending failed. Check error messages above.")
            sys.exit(1)
    else:
        print("\n✅ Authentication test complete. Skipped email sending.")

if __name__ == "__main__":
    main()