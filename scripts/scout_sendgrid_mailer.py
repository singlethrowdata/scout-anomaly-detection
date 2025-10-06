#!/usr/bin/env python3
"""
SCOUT Gmail Email Mailer
[R9]: Morning email digest with all anomalies
→ needs: email-notifications (HTML from digest generator)
→ provides: gmail-smtp-delivery

Sends daily SCOUT email digest via Gmail SMTP.
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add custom pip packages directory to path (Windows Store Python workaround)
sys.path.insert(0, 'C:\\pippackages')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


def load_email_content() -> tuple[str, Dict[str, Any]]:
    """
    Load generated email HTML and metadata.
    [R9]: Load consolidated digest from generator

    Returns:
        Tuple of (html_content, metadata)
    """
    data_dir = Path(__file__).parent.parent / "data"

    # Load HTML content
    html_path = data_dir / "scout_daily_digest_preview.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Load metadata
    metadata_path = data_dir / "scout_email_metadata.json"
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    return html_content, metadata


def send_email_digest(
    html_content: str,
    metadata: Dict[str, Any],
    recipients: List[str]
) -> Dict[str, Any]:
    """
    Send email digest via Gmail SMTP.
    [R9]: Gmail SMTP integration with delivery tracking

    Args:
        html_content: HTML email content
        metadata: Email metadata with alert counts
        recipients: List of recipient email addresses

    Returns:
        Delivery status and response
    """
    # Get Gmail credentials from environment
    gmail_user = os.getenv('GMAIL_USER')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user or not gmail_app_password:
        return {
            'success': False,
            'error': 'Missing GMAIL_USER or GMAIL_APP_PASSWORD in .env file',
            'recipients': recipients,
            'timestamp': datetime.now().isoformat()
        }

    # Generate subject line based on alert counts
    total_alerts = metadata.get('total_alerts', 0)
    disaster_count = metadata['alert_counts']['disasters']

    if disaster_count > 0:
        subject = f"🚨 SCOUT Alert: {disaster_count} CRITICAL Disasters + {total_alerts - disaster_count} Other Anomalies"
    elif total_alerts > 0:
        subject = f"⚠️ SCOUT Daily Report: {total_alerts} Anomalies Detected"
    else:
        subject = "✅ SCOUT Daily Report: All Clear"

    # Send via Gmail SMTP
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"SCOUT Anomaly Detection <{gmail_user}>"
        message['To'] = ', '.join(recipients)

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, recipients, message.as_string())

        return {
            'success': True,
            'response': 'Email sent via Gmail SMTP',
            'recipients': recipients,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'recipients': recipients,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }


def save_delivery_log(delivery_status: Dict[str, Any]) -> None:
    """
    Save delivery log for tracking.
    [R9]: Delivery tracking and audit trail
    """
    logs_dir = Path(__file__).parent.parent / "data" / "email_logs"
    logs_dir.mkdir(exist_ok=True)

    log_filename = f"scout_email_delivery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path = logs_dir / log_filename

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(delivery_status, f, indent=2)

    print(f"   ✅ Delivery log saved: {log_path}")


def main():
    """
    Main execution: Load digest, send via Gmail SMTP, log delivery.
    [R9]: Email digest delivery workflow
    """
    print("[R9] SCOUT Gmail Email Mailer")
    print("=" * 60)

    # Get recipient list from environment variable or use default
    recipients_str = os.getenv('SCOUT_EMAIL_RECIPIENTS', '')
    if not recipients_str:
        print("\n⚠️  WARNING: No recipients configured")
        print("   Set SCOUT_EMAIL_RECIPIENTS in .env file")
        print("   Using default: submissions@singlethrow.com")
        recipients = ['submissions@singlethrow.com']
    else:
        recipients = [email.strip() for email in recipients_str.split(',')]

    print(f"\n1. Loading email digest...")
    html_content, metadata = load_email_content()
    print(f"   - Properties analyzed: {metadata['properties_analyzed']}")
    print(f"   - Total alerts: {metadata['total_alerts']}")
    print(f"   - Alert breakdown:")
    for detector, count in metadata['alert_counts'].items():
        print(f"     * {detector}: {count}")

    print(f"\n2. Preparing Gmail SMTP delivery...")
    print(f"   - Recipients: {', '.join(recipients)}")
    print(f"   - Generated at: {metadata['generated_at']}")

    # Send email
    print(f"\n3. Sending email digest via Gmail SMTP...")
    delivery_status = send_email_digest(html_content, metadata, recipients)

    if delivery_status['success']:
        print(f"   ✅ Email sent successfully!")
        print(f"   - Response: {delivery_status['response']}")
        print(f"   - Recipients: {len(recipients)}")
    else:
        print(f"   ❌ Email delivery failed!")
        print(f"   - Error: {delivery_status['error']}")

    # Save delivery log
    print(f"\n4. Saving delivery log...")
    save_delivery_log(delivery_status)

    print(f"\n5. Email digest delivery complete!")
    if delivery_status['success']:
        print(f"   - Check recipient inbox: {', '.join(recipients)}")
        print(f"   - Subject: {delivery_status['subject']}")
    else:
        print(f"   - Check Gmail credentials in .env file")


if __name__ == "__main__":
    main()

