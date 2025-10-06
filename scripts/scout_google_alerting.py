"""
SCOUT Google Workspace Alerting System [R9-R10]
Uses Gmail API and Google Chat for internal team notifications
No external costs - leverages existing Google Cloud infrastructure
"""

import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import requests

# Google API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertPriority(Enum):
    """Alert priority levels with Scout Tower gradient colors"""
    CRITICAL = ("red", "#E74C3C", 70)  # High impact score threshold
    WARNING = ("yellow", "#F39C12", 40)  # Medium impact score threshold
    NORMAL = ("green", "#6B8F71", 0)    # Low impact score threshold

@dataclass
class Alert:
    """Individual alert with business context"""
    client_name: str
    property_id: str
    metric: str
    date: str
    current_value: float
    expected_value: float
    deviation_percent: float
    impact_score: float
    priority: AlertPriority
    detection_method: str
    business_impact: str

class SCOUTGoogleAlerting:
    """SCOUT alerting via Google Workspace APIs - zero external costs"""

    def __init__(self, service_account_file: str = None):
        """
        Initialize with Google service account (same as BigQuery)

        Args:
            service_account_file: Path to service account JSON file
                                 Falls back to GOOGLE_APPLICATION_CREDENTIALS env var
        """
        # [R9]: Initialize Google Workspace authentication
        self.service_account_file = service_account_file or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        if not self.service_account_file:
            raise ValueError("Service account file required. Set GOOGLE_APPLICATION_CREDENTIALS or provide path")

        # Create credentials with necessary scopes
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=[
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/chat.bot'
            ]
        )

        # Build Gmail service
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)

        # Alert thresholds
        self.critical_threshold = 70
        self.warning_threshold = 40

        print(f"✅ SCOUT Google Alerting initialized with service account")

    def load_anomalies(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load anomaly detection results from JSON file

        Args:
            file_path: Path to anomaly JSON file

        Returns:
            List of anomaly records
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract anomalies from the results
        anomalies = []
        property_id = data.get('property_id', 'unknown')

        if 'results' in data:
            for metric_data in data['results']:
                metric = metric_data['metric']
                for point in metric_data.get('data_points', []):
                    if point.get('is_anomaly', False):
                        anomalies.append({
                            'property_id': property_id,
                            'metric': metric,
                            'date': point['date'],
                            'value': point['value'],
                            'baseline_mean': metric_data['statistical_summary']['mean'],
                            'z_score': point.get('z_score', 0),
                            'iqr_outlier': point.get('iqr_outlier', False),
                            'detection_method': point.get('detection_methods', [])
                        })

        return anomalies

    def classify_alerts(self, anomalies: List[Dict[str, Any]], client_name: str = "Client") -> List[Alert]:
        """
        Convert anomalies to classified alerts with business impact

        Args:
            anomalies: List of anomaly records
            client_name: Name of the client

        Returns:
            List of Alert objects with priority classification
        """
        alerts = []

        for anomaly in anomalies:
            # Calculate deviation percentage
            baseline = anomaly.get('baseline_mean', 0)
            current = anomaly.get('value', 0)
            if baseline > 0:
                deviation_pct = abs((current - baseline) / baseline * 100)
            else:
                deviation_pct = 100 if current > 0 else 0

            # Calculate impact score [R6]
            impact_score = self._calculate_impact_score(
                anomaly['metric'],
                deviation_pct,
                current < baseline
            )

            # Determine priority
            if impact_score >= self.critical_threshold:
                priority = AlertPriority.CRITICAL
            elif impact_score >= self.warning_threshold:
                priority = AlertPriority.WARNING
            else:
                priority = AlertPriority.NORMAL

            # Generate business impact description
            business_impact = self._generate_business_impact(
                anomaly['metric'],
                deviation_pct,
                current < baseline
            )

            # Determine detection method
            methods = anomaly.get('detection_method', [])
            if 'z_score' in methods and 'iqr' in methods:
                detection_method = "Statistical consensus (Z-score + IQR)"
            elif 'z_score' in methods:
                detection_method = f"Z-score anomaly ({anomaly.get('z_score', 0):.2f} std dev)"
            elif 'iqr' in methods:
                detection_method = "IQR outlier detection"
            else:
                detection_method = "Pattern recognition"

            alerts.append(Alert(
                client_name=client_name,
                property_id=anomaly.get('property_id', 'unknown'),
                metric=anomaly['metric'],
                date=anomaly['date'],
                current_value=current,
                expected_value=baseline,
                deviation_percent=deviation_pct,
                impact_score=impact_score,
                priority=priority,
                detection_method=detection_method,
                business_impact=business_impact
            ))

        return alerts

    def _calculate_impact_score(self, metric: str, deviation_pct: float, is_drop: bool) -> float:
        """
        Calculate business impact score (0-100)

        Args:
            metric: Metric name
            deviation_pct: Percentage deviation from baseline
            is_drop: Whether this is a decrease

        Returns:
            Impact score from 0-100
        """
        # Base score from deviation
        base_score = min(deviation_pct / 2, 50)

        # Metric importance weights [R6]
        metric_weights = {
            'conversions': 2.0,
            'users': 1.2,
            'sessions': 1.0,
            'page_views': 0.8
        }

        weight = metric_weights.get(metric.lower(), 1.0)

        # Drops more concerning than spikes
        direction_multiplier = 1.5 if is_drop else 1.0

        # Calculate final score
        score = base_score * weight * direction_multiplier

        return min(score, 100)

    def _generate_business_impact(self, metric: str, deviation_pct: float, is_drop: bool) -> str:
        """
        Generate human-readable business impact description
        """
        direction = "decrease" if is_drop else "increase"
        severity = "significant" if deviation_pct > 50 else "notable"

        impacts = {
            'conversions': {
                True: f"{severity.capitalize()} revenue impact - {deviation_pct:.1f}% conversion drop requires immediate attention",
                False: f"Positive conversion spike of {deviation_pct:.1f}% - verify tracking and capitalize on success"
            },
            'users': {
                True: f"User acquisition down {deviation_pct:.1f}% - potential traffic or targeting issue",
                False: f"User growth up {deviation_pct:.1f}% - monitor for quality and engagement"
            },
            'sessions': {
                True: f"Session volume dropped {deviation_pct:.1f}% - check site availability and campaigns",
                False: f"Session increase of {deviation_pct:.1f}% - ensure infrastructure can handle load"
            },
            'page_views': {
                True: f"Page views down {deviation_pct:.1f}% - possible navigation or content issues",
                False: f"Page view surge of {deviation_pct:.1f}% - good engagement signal"
            }
        }

        metric_lower = metric.lower()
        if metric_lower in impacts:
            return impacts[metric_lower][is_drop]

        return f"{severity.capitalize()} {direction} of {deviation_pct:.1f}% detected"

    def generate_email_html(self, alerts: List[Alert], date: Optional[datetime] = None) -> str:
        """
        Generate HTML email content with SCOUT branding [AR1]
        """
        if date is None:
            date = datetime.now()

        # Count alerts by priority
        critical_count = len([a for a in alerts if a.priority == AlertPriority.CRITICAL])
        warning_count = len([a for a in alerts if a.priority == AlertPriority.WARNING])
        normal_count = len([a for a in alerts if a.priority == AlertPriority.NORMAL])

        # Build HTML with SCOUT branding
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f5f5f5;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 8px;">

                            <!-- Header with STM Blue -->
                            <tr>
                                <td style="background-color: #1A5276; padding: 40px; border-radius: 8px 8px 0 0;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 32px; text-align: center;">SCOUT</h1>
                                    <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px; text-align: center;">
                                        Daily Reconnaissance Report - {date.strftime('%B %d, %Y')}
                                    </p>
                                </td>
                            </tr>

                            <!-- Gradient Bar [AR1] -->
                            <tr>
                                <td style="background: linear-gradient(90deg, #6B8F71 0%, #F39C12 50%, #E74C3C 100%); height: 4px;"></td>
                            </tr>

                            <!-- Summary Content -->
                            <tr>
                                <td style="padding: 40px;">
                                    <p style="color: #24292E; font-size: 16px;">Good morning,</p>
                                    <p style="color: #24292E;">SCOUT completed overnight reconnaissance. Here's what needs attention:</p>

                                    <!-- Alert Summary Boxes -->
                                    <table width="100%" style="margin: 30px 0;">
                                        <tr>
                                            <td width="33%" align="center" style="padding: 20px; background: #f8f9fa;">
                                                <div style="color: #E74C3C; font-size: 36px; font-weight: 700;">{critical_count}</div>
                                                <div style="color: #6E6F71; font-size: 12px;">CRITICAL</div>
                                            </td>
                                            <td width="33%" align="center">
                                                <div style="color: #F39C12; font-size: 36px; font-weight: 700;">{warning_count}</div>
                                                <div style="color: #6E6F71; font-size: 12px;">WARNING</div>
                                            </td>
                                            <td width="33%" align="center" style="padding: 20px; background: #f8f9fa;">
                                                <div style="color: #6B8F71; font-size: 36px; font-weight: 700;">{normal_count}</div>
                                                <div style="color: #6E6F71; font-size: 12px;">NORMAL</div>
                                            </td>
                                        </tr>
                                    </table>

                                    {self._generate_alert_details_html(alerts)}

                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="padding: 30px; background: #f8f9fa; border-radius: 0 0 8px 8px;">
                                    <p style="margin: 0; color: #6E6F71; font-size: 12px; text-align: center;">
                                        SCOUT - Always watching. Always ready.<br>
                                        Single Throw Marketing
                                    </p>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        return html

    def _generate_alert_details_html(self, alerts: List[Alert]) -> str:
        """Generate HTML for individual alert details"""
        if not alerts:
            return """
            <div style="padding: 20px; background: #f8f9fa; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #6B8F71; text-align: center;">
                    ✓ No anomalies detected - All systems normal
                </p>
            </div>
            """

        # Sort by impact score
        alerts_sorted = sorted(alerts, key=lambda a: a.impact_score, reverse=True)

        html_parts = ['<div style="margin-top: 30px;">']
        html_parts.append('<h3 style="color: #24292E; margin-bottom: 20px;">Detailed Findings</h3>')

        # Group by priority
        for priority in [AlertPriority.CRITICAL, AlertPriority.WARNING]:  # Skip NORMAL for brevity
            priority_alerts = [a for a in alerts_sorted if a.priority == priority]
            if priority_alerts:
                html_parts.append(f'''
                <div style="margin: 20px 0;">
                    <div style="display: inline-block; padding: 4px 12px; background: {priority.value[1]}20;
                                border-left: 3px solid {priority.value[1]}; margin-bottom: 15px;">
                        <span style="color: {priority.value[1]}; font-weight: 600; font-size: 14px;">
                            {priority.name} ({len(priority_alerts)})
                        </span>
                    </div>
                ''')

                # Add top alerts
                for alert in priority_alerts[:3]:  # Limit to top 3 per category
                    html_parts.append(f'''
                    <div style="background: white; border: 1px solid #e1e4e8; border-radius: 4px;
                                padding: 15px; margin-bottom: 10px;">
                        <h4 style="margin: 0 0 8px 0; color: #24292E; font-size: 16px;">
                            {alert.client_name} - {alert.metric.replace('_', ' ').title()}
                        </h4>
                        <p style="margin: 5px 0; color: #586069; font-size: 14px;">
                            {alert.business_impact}
                        </p>
                        <div style="margin-top: 10px; font-size: 12px; color: #6E6F71;">
                            Current: {alert.current_value:.0f} | Expected: {alert.expected_value:.0f} |
                            Deviation: {alert.deviation_percent:.1f}%
                        </div>
                    </div>
                    ''')

                html_parts.append('</div>')

        html_parts.append('</div>')
        return ''.join(html_parts)

    def send_email_digest(self, alerts: List[Alert], recipients: List[str], test_mode: bool = False) -> bool:
        """
        Send email digest via Gmail API [R9]

        Args:
            alerts: List of alerts to send
            recipients: List of email addresses
            test_mode: If True, saves HTML preview without sending

        Returns:
            Success status
        """
        try:
            # Generate HTML content
            html_content = self.generate_email_html(alerts)

            if test_mode:
                # Save preview for testing
                output_path = Path(__file__).parent.parent / 'data' / 'scout_email_preview.html'
                with open(output_path, 'w') as f:
                    f.write(html_content)
                print(f"✅ Email preview saved to: {output_path}")
                return True

            # Create message
            message = MIMEMultipart('alternative')

            # Email headers
            critical_count = len([a for a in alerts if a.priority == AlertPriority.CRITICAL])
            subject = f"SCOUT Daily Report - {critical_count} Critical Alert{'s' if critical_count != 1 else ''}" if critical_count > 0 else "SCOUT Daily Report - All Systems Normal"

            message['Subject'] = subject
            message['From'] = 'scout@singlethrow.com'
            message['To'] = ', '.join(recipients)

            # Attach HTML
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Send via Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_message = {'raw': raw_message}

            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            print(f"✅ Email sent successfully to {len(recipients)} recipients")
            print(f"   Message ID: {sent_message['id']}")
            return True

        except HttpError as error:
            print(f"❌ Gmail API error: {error}")
            return False
        except Exception as e:
            print(f"❌ Error sending email: {str(e)}")
            return False

    def send_chat_alert(self, alert: Alert, webhook_url: str) -> bool:
        """
        Send critical alert to Google Chat space [R10]

        Args:
            alert: Alert to send (typically critical only)
            webhook_url: Google Chat webhook URL

        Returns:
            Success status
        """
        try:
            # Create Google Chat card
            card_message = {
                "cards": [{
                    "header": {
                        "title": f"🚨 {alert.priority.name} ALERT",
                        "subtitle": f"{alert.client_name} - {alert.date}",
                        "imageUrl": "https://fonts.gstatic.com/s/i/productlogos/chat/v9/web-64dp/logo_chat_color_1x_web_64dp.png"
                    },
                    "sections": [{
                        "header": f"{alert.metric.replace('_', ' ').title()} Anomaly Detected",
                        "widgets": [
                            {
                                "keyValue": {
                                    "topLabel": "Current Value",
                                    "content": f"{alert.current_value:.0f}",
                                    "icon": "DESCRIPTION"
                                }
                            },
                            {
                                "keyValue": {
                                    "topLabel": "Expected Value",
                                    "content": f"{alert.expected_value:.0f}",
                                    "icon": "EVENT_SEAT"
                                }
                            },
                            {
                                "keyValue": {
                                    "topLabel": "Deviation",
                                    "content": f"{alert.deviation_percent:.1f}%",
                                    "icon": "FLIGHT_TAKEOFF"
                                }
                            },
                            {
                                "keyValue": {
                                    "topLabel": "Impact Score",
                                    "content": f"{alert.impact_score:.0f}/100",
                                    "icon": "STAR" if alert.impact_score >= 70 else "BOOKMARK"
                                }
                            },
                            {
                                "textParagraph": {
                                    "text": f"<b>Business Impact:</b><br>{alert.business_impact}"
                                }
                            },
                            {
                                "buttons": [{
                                    "textButton": {
                                        "text": "VIEW IN GA4",
                                        "onClick": {
                                            "openLink": {
                                                "url": f"https://analytics.google.com/analytics/web/#/p{alert.property_id}/reports"
                                            }
                                        }
                                    }
                                }]
                            }
                        ]
                    }]
                }]
            }

            # Send to Google Chat
            response = requests.post(
                webhook_url,
                json=card_message,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                print(f"✅ Chat alert sent for {alert.client_name} - {alert.metric}")
                return True
            else:
                print(f"❌ Chat send failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending Chat alert: {str(e)}")
            return False

    def process_and_alert(
        self,
        anomaly_file: str,
        client_name: str,
        email_recipients: List[str],
        chat_webhook: str = None
    ) -> Dict[str, Any]:
        """
        Main processing function - load anomalies and send alerts

        Args:
            anomaly_file: Path to anomaly JSON file
            client_name: Name of the client
            email_recipients: List of email addresses for digest
            chat_webhook: Optional Google Chat webhook for critical alerts

        Returns:
            Processing results dictionary
        """
        print(f"\n🔍 SCOUT Google Alerting - Processing {client_name}")
        print("=" * 60)

        # Load anomalies
        anomalies = self.load_anomalies(anomaly_file)

        if not anomalies:
            print("✅ No anomalies detected - all systems normal")
            # Still send "all clear" email
            self.send_email_digest([], email_recipients, test_mode=True)
            return {
                "total_anomalies": 0,
                "email_sent": True,
                "chat_alerts_sent": 0
            }

        print(f"📊 Loaded {len(anomalies)} anomalies from detection results")

        # Classify into alerts
        alerts = self.classify_alerts(anomalies, client_name)

        # Count by priority
        critical = [a for a in alerts if a.priority == AlertPriority.CRITICAL]
        warning = [a for a in alerts if a.priority == AlertPriority.WARNING]
        normal = [a for a in alerts if a.priority == AlertPriority.NORMAL]

        print(f"\n📈 Alert Classification:")
        print(f"  🔴 Critical: {len(critical)} alerts (impact ≥ {self.critical_threshold})")
        print(f"  🟡 Warning: {len(warning)} alerts (impact ≥ {self.warning_threshold})")
        print(f"  🟢 Normal: {len(normal)} alerts")

        # Send email digest [R9]
        email_sent = self.send_email_digest(alerts, email_recipients, test_mode=True)

        # Send Chat alerts for critical items [R10]
        chat_sent = 0
        if chat_webhook:
            for alert in critical:
                if self.send_chat_alert(alert, chat_webhook):
                    chat_sent += 1

        results = {
            "total_anomalies": len(anomalies),
            "total_alerts": len(alerts),
            "critical": len(critical),
            "warning": len(warning),
            "normal": len(normal),
            "email_sent": email_sent,
            "chat_alerts_sent": chat_sent,
            "top_alerts": [
                {
                    "client": a.client_name,
                    "metric": a.metric,
                    "impact": a.impact_score,
                    "deviation": a.deviation_percent,
                    "business_impact": a.business_impact
                }
                for a in sorted(alerts, key=lambda x: x.impact_score, reverse=True)[:5]
            ]
        }

        # Save results
        output_file = Path(__file__).parent.parent / 'data' / f'scout_alerts_{client_name.lower().replace(" ", "_")}.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Alert processing complete!")
        print(f"📁 Results saved to: {output_file}")

        return results


def main():
    """Test the Google Workspace alerting system"""

    # Initialize with service account
    try:
        alerting = SCOUTGoogleAlerting()

        # Process existing anomaly data
        anomaly_file = Path(__file__).parent.parent / 'data' / 'scout_anomalies_249571600.json'

        if anomaly_file.exists():
            results = alerting.process_and_alert(
                str(anomaly_file),
                client_name="SingleThrow",
                email_recipients=['am-team@singlethrow.com'],
                chat_webhook=os.getenv('GOOGLE_CHAT_WEBHOOK_URL')  # Optional
            )

            print("\n📊 Summary:")
            print(json.dumps(results, indent=2))
        else:
            print(f"❌ Anomaly file not found: {anomaly_file}")
            print("Run scout_anomaly_detector.py first to generate anomaly data")

    except Exception as e:
        print(f"❌ Error initializing alerting: {str(e)}")
        print("Ensure GOOGLE_APPLICATION_CREDENTIALS is set to service account JSON path")


if __name__ == "__main__":
    main()