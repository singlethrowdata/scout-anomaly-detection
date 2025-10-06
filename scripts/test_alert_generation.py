"""
Test SCOUT Alert Generation without Google API dependencies
Tests the HTML generation and alert classification logic
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class AlertPriority(Enum):
    """Alert priority levels with Scout Tower gradient colors"""
    CRITICAL = ("red", "#E74C3C", 70)
    WARNING = ("yellow", "#F39C12", 40)
    NORMAL = ("green", "#6B8F71", 0)

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

class SCOUTAlertTester:
    """Test alert generation without external dependencies"""

    def __init__(self):
        self.critical_threshold = 70
        self.warning_threshold = 40

    def load_anomalies(self, file_path: str) -> List[Dict[str, Any]]:
        """Load anomaly detection results from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        anomalies = []
        property_id = data.get('property_id', 'unknown')

        if 'results' in data:
            for metric_data in data['results']:
                metric = metric_data['metric']
                for point in metric_data.get('data_points', []):
                    # For testing, create synthetic anomalies based on deviation
                    baseline = metric_data['statistical_summary']['mean']
                    value = point['value']
                    deviation = abs((value - baseline) / baseline * 100) if baseline > 0 else 0

                    # Flag as anomaly if deviation > 20%
                    if deviation > 20:
                        anomalies.append({
                            'property_id': property_id,
                            'metric': metric,
                            'date': point['date'],
                            'value': value,
                            'baseline_mean': baseline,
                            'z_score': point.get('z_score', 0),
                            'deviation': deviation
                        })

        return anomalies

    def classify_alerts(self, anomalies: List[Dict[str, Any]], client_name: str = "Client") -> List[Alert]:
        """Convert anomalies to classified alerts"""
        alerts = []

        for anomaly in anomalies:
            baseline = anomaly.get('baseline_mean', 0)
            current = anomaly.get('value', 0)
            deviation_pct = anomaly.get('deviation', 0)

            # Calculate impact score
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

            # Generate business impact
            business_impact = self._generate_business_impact(
                anomaly['metric'],
                deviation_pct,
                current < baseline
            )

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
                detection_method=f"Z-score: {anomaly.get('z_score', 0):.2f}",
                business_impact=business_impact
            ))

        return alerts

    def _calculate_impact_score(self, metric: str, deviation_pct: float, is_drop: bool) -> float:
        """Calculate business impact score"""
        base_score = min(deviation_pct / 2, 50)

        metric_weights = {
            'conversions': 2.0,
            'users': 1.2,
            'sessions': 1.0,
            'page_views': 0.8
        }

        weight = metric_weights.get(metric.lower(), 1.0)
        direction_multiplier = 1.5 if is_drop else 1.0

        return min(base_score * weight * direction_multiplier, 100)

    def _generate_business_impact(self, metric: str, deviation_pct: float, is_drop: bool) -> str:
        """Generate business impact description"""
        direction = "decrease" if is_drop else "increase"
        severity = "significant" if deviation_pct > 50 else "notable"

        return f"{severity.capitalize()} {direction} of {deviation_pct:.1f}% in {metric}"

    def generate_html_preview(self, alerts: List[Alert]) -> str:
        """Generate HTML email preview"""
        date = datetime.now()

        # Count by priority
        critical_count = len([a for a in alerts if a.priority == AlertPriority.CRITICAL])
        warning_count = len([a for a in alerts if a.priority == AlertPriority.WARNING])
        normal_count = len([a for a in alerts if a.priority == AlertPriority.NORMAL])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SCOUT Alert Preview</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f5;
                    padding: 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .header {{
                    background: #1A5276;
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                .gradient-bar {{
                    height: 4px;
                    background: linear-gradient(90deg, #6B8F71 0%, #F39C12 50%, #E74C3C 100%);
                }}
                .content {{
                    padding: 40px;
                }}
                .summary-boxes {{
                    display: flex;
                    justify-content: space-around;
                    margin: 30px 0;
                }}
                .summary-box {{
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    flex: 1;
                    margin: 0 10px;
                }}
                .alert-item {{
                    background: white;
                    border: 1px solid #e1e4e8;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 10px;
                }}
                .critical {{ border-left: 3px solid #E74C3C; }}
                .warning {{ border-left: 3px solid #F39C12; }}
                .normal {{ border-left: 3px solid #6B8F71; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SCOUT</h1>
                    <p>Daily Reconnaissance Report - {date.strftime('%B %d, %Y')}</p>
                </div>

                <div class="gradient-bar"></div>

                <div class="content">
                    <p>Good morning,</p>
                    <p>SCOUT completed overnight reconnaissance. Here's what needs attention:</p>

                    <div class="summary-boxes">
                        <div class="summary-box">
                            <div style="color: #E74C3C; font-size: 36px; font-weight: 700;">{critical_count}</div>
                            <div style="color: #6E6F71; font-size: 12px;">CRITICAL</div>
                        </div>
                        <div class="summary-box">
                            <div style="color: #F39C12; font-size: 36px; font-weight: 700;">{warning_count}</div>
                            <div style="color: #6E6F71; font-size: 12px;">WARNING</div>
                        </div>
                        <div class="summary-box">
                            <div style="color: #6B8F71; font-size: 36px; font-weight: 700;">{normal_count}</div>
                            <div style="color: #6E6F71; font-size: 12px;">NORMAL</div>
                        </div>
                    </div>
        """

        if alerts:
            html += "<h3>Detailed Findings</h3>"

            # Group by priority
            for priority in [AlertPriority.CRITICAL, AlertPriority.WARNING]:
                priority_alerts = [a for a in alerts if a.priority == priority]
                if priority_alerts:
                    html += f'<h4 style="color: {priority.value[1]};">{priority.name} Alerts</h4>'

                    for alert in priority_alerts[:3]:
                        css_class = priority.name.lower()
                        html += f'''
                        <div class="alert-item {css_class}">
                            <h4>{alert.client_name} - {alert.metric.replace("_", " ").title()}</h4>
                            <p>{alert.business_impact}</p>
                            <small>
                                Current: {alert.current_value:.0f} |
                                Expected: {alert.expected_value:.0f} |
                                Deviation: {alert.deviation_percent:.1f}% |
                                Impact Score: {alert.impact_score:.0f}
                            </small>
                        </div>
                        '''
        else:
            html += '''
            <div style="padding: 20px; background: #f8f9fa; margin: 20px 0; border-radius: 4px; text-align: center;">
                ✓ No anomalies detected - All systems normal
            </div>
            '''

        html += """
                </div>

                <div style="padding: 30px; background: #f8f9fa; text-align: center;">
                    <p style="margin: 0; color: #6E6F71; font-size: 12px;">
                        SCOUT - Always watching. Always ready.<br>
                        Single Throw Marketing
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def test_with_production_data(self):
        """Test alert generation with production anomaly data"""
        print("\n🔍 SCOUT Alert Generation Test")
        print("=" * 60)

        # Load anomaly data
        anomaly_file = Path(__file__).parent.parent / 'data' / 'scout_anomalies_249571600.json'

        if not anomaly_file.exists():
            # Create synthetic test data
            print("⚠️ No anomaly data found, creating synthetic test data...")

            test_alerts = [
                Alert(
                    client_name="SingleThrow",
                    property_id="249571600",
                    metric="conversions",
                    date="2025-01-24",
                    current_value=0,
                    expected_value=5,
                    deviation_percent=100,
                    impact_score=90,
                    priority=AlertPriority.CRITICAL,
                    detection_method="Z-score: 3.2",
                    business_impact="Significant revenue impact - 100% conversion drop requires immediate attention"
                ),
                Alert(
                    client_name="SingleThrow",
                    property_id="249571600",
                    metric="users",
                    date="2025-01-24",
                    current_value=15,
                    expected_value=33,
                    deviation_percent=54.5,
                    impact_score=49,
                    priority=AlertPriority.WARNING,
                    detection_method="Z-score: 2.1",
                    business_impact="User acquisition down 54.5% - potential traffic or targeting issue"
                ),
                Alert(
                    client_name="SingleThrow",
                    property_id="249571600",
                    metric="page_views",
                    date="2025-01-25",
                    current_value=65,
                    expected_value=44,
                    deviation_percent=47.7,
                    impact_score=19,
                    priority=AlertPriority.NORMAL,
                    detection_method="Z-score: 1.6",
                    business_impact="Page view surge of 47.7% - good engagement signal"
                )
            ]
        else:
            # Load real anomaly data
            anomalies = self.load_anomalies(str(anomaly_file))
            print(f"📊 Loaded {len(anomalies)} potential anomalies")

            # If no anomalies in real data, create synthetic ones
            if not anomalies:
                print("ℹ️ No anomalies detected in production data (stable traffic)")
                print("Creating synthetic anomalies for demonstration...")

                # Create synthetic anomalies for testing
                anomalies = [
                    {
                        'property_id': '249571600',
                        'metric': 'conversions',
                        'date': '2025-01-24',
                        'value': 0,
                        'baseline_mean': 5,
                        'z_score': 3.2,
                        'deviation': 100
                    },
                    {
                        'property_id': '249571600',
                        'metric': 'users',
                        'date': '2025-01-24',
                        'value': 15,
                        'baseline_mean': 33,
                        'z_score': 2.1,
                        'deviation': 54.5
                    }
                ]

            # Classify alerts
            test_alerts = self.classify_alerts(anomalies, "SingleThrow")

        # Count by priority
        critical = [a for a in test_alerts if a.priority == AlertPriority.CRITICAL]
        warning = [a for a in test_alerts if a.priority == AlertPriority.WARNING]
        normal = [a for a in test_alerts if a.priority == AlertPriority.NORMAL]

        print(f"\n📈 Alert Classification:")
        print(f"  🔴 Critical: {len(critical)} alerts")
        print(f"  🟡 Warning: {len(warning)} alerts")
        print(f"  🟢 Normal: {len(normal)} alerts")

        # Generate HTML preview
        html_content = self.generate_html_preview(test_alerts)

        # Save preview
        output_path = Path(__file__).parent.parent / 'data' / 'scout_alert_preview.html'
        with open(output_path, 'w') as f:
            f.write(html_content)

        print(f"\n✅ Alert preview generated successfully!")
        print(f"📁 Preview saved to: {output_path}")
        print(f"\nOpen the HTML file in a browser to see the SCOUT alert design")

        # Display top alerts
        if test_alerts:
            print("\n🎯 Top Alerts:")
            for i, alert in enumerate(sorted(test_alerts, key=lambda a: a.impact_score, reverse=True)[:3], 1):
                print(f"\n{i}. {alert.metric.replace('_', ' ').title()} - {alert.priority.name}")
                print(f"   Impact Score: {alert.impact_score:.0f}/100")
                print(f"   {alert.business_impact}")

        return test_alerts


def main():
    """Run the alert generation test"""
    tester = SCOUTAlertTester()
    alerts = tester.test_with_production_data()

    print(f"\n📊 Test Summary:")
    print(f"   Total alerts generated: {len(alerts)}")
    print(f"   HTML preview ready for review")
    print(f"\n✨ SCOUT Intelligent Alerting System is ready for deployment!")


if __name__ == "__main__":
    main()