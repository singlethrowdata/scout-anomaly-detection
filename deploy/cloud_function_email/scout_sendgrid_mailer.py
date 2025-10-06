#!/usr/bin/env python3
"""
SCOUT Gmail Email Mailer
[R9]: Morning email digest with all anomalies
→ needs: email-notifications (HTML from digest generator)
→ provides: gmail-smtp-delivery

Sends daily SCOUT email digest via Gmail SMTP.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any


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
    # Get Gmail credentials from environment (Cloud Functions env vars)
    gmail_user = os.getenv('GMAIL_USER')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user or not gmail_app_password:
        return {
            'success': False,
            'error': 'Missing GMAIL_USER or GMAIL_APP_PASSWORD environment variables',
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

