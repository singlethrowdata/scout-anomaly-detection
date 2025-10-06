# [R9] Cloud Function for daily email digest
# → needs: email-digest-generator, gmail-smtp-mailer
# → provides: cloud-scheduler-endpoint

import os
import sys
import json
from datetime import datetime
import functions_framework

# Add current directory to path to import SCOUT modules
sys.path.insert(0, os.path.dirname(__file__))

from scout_email_digest_generator import load_detector_alerts, generate_html_email
from scout_sendgrid_mailer import send_email_digest

@functions_framework.http
def send_daily_digest(request):
    """
    [R9]: Cloud Function to send daily SCOUT email digest
    → needs: prioritized-alerts
    → provides: email-notifications

    Triggered by Cloud Scheduler at 7 AM ET daily
    """
    try:
        # Load all 4 detector alerts from Cloud Storage
        alerts_data = load_detector_alerts()

        # Generate HTML email
        html_content = generate_html_email(alerts_data)

        # Get recipient list from environment variable
        recipients_str = os.getenv('SCOUT_EMAIL_RECIPIENTS', '')
        recipients = [email.strip() for email in recipients_str.split(',')]

        # Prepare metadata for email mailer
        metadata = {
            'generated_at': alerts_data['metadata']['generated_at'],
            'properties_analyzed': alerts_data['metadata']['properties_analyzed'],
            'total_alerts': alerts_data['metadata']['total_alerts'],
            'alert_counts': {
                'disasters': len(alerts_data['disasters']),
                'spam': len(alerts_data['spam']),
                'records': len(alerts_data['records']),
                'trends': len(alerts_data['trends'])
            }
        }

        # Send email via Gmail SMTP
        delivery_status = send_email_digest(html_content, metadata, recipients)

        if delivery_status['success']:
            return (
                json.dumps({
                    "status": "success",
                    "message": "Email sent successfully",
                    "alerts_count": alerts_data['metadata']['total_alerts'],
                    "recipients": len(recipients)
                }),
                200,
                {'Content-Type': 'application/json'}
            )
        else:
            return (
                json.dumps({
                    "status": "error",
                    "message": delivery_status.get('error', 'Email delivery failed')
                }),
                500,
                {'Content-Type': 'application/json'}
            )

    except Exception as e:
        print(f"Error in send_daily_digest: {str(e)}")
        import traceback
        traceback.print_exc()
        return (
            json.dumps({
                "status": "error",
                "message": str(e)
            }),
            500,
            {'Content-Type': 'application/json'}
        )
