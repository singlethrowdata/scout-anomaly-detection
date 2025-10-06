#!/usr/bin/env python3
"""
SCOUT Daily Email Digest Generator
[R9]: Morning email digest with all anomalies
→ needs: prioritized-alerts
→ provides: email-notifications

Consolidates all 4 detector outputs into single daily email digest.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# [R9]: Import STM brand colors for consistent email styling
from scout_brand_config import STM_COLORS, EMAIL_STYLES, get_status_color


def load_detector_alerts() -> Dict[str, Any]:
    """
    Load all 4 detector alert JSONs from data/ directory.
    [R9]: Consolidate disaster, spam, record, trend alerts

    Returns:
        Dict with detector results and metadata
    """
    data_dir = Path(__file__).parent.parent / "data"

    detectors = {
        'disasters': data_dir / "scout_disaster_alerts.json",
        'spam': data_dir / "scout_spam_alerts.json",
        'records': data_dir / "scout_record_alerts.json",
        'trends': data_dir / "scout_trend_alerts.json"
    }

    results = {
        'disasters': [],
        'spam': [],
        'records': [],
        'trends': [],
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'properties_analyzed': set(),
            'total_alerts': 0
        }
    }

    for detector_name, file_path in detectors.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results[detector_name] = data.get('alerts', [])
                results['metadata']['properties_analyzed'].add(
                    data.get('properties_analyzed', 0)
                )
                results['metadata']['total_alerts'] += len(data.get('alerts', []))
        except FileNotFoundError:
            print(f"Warning: {file_path} not found, skipping {detector_name}")
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")

    # Convert set to max value for properties analyzed
    results['metadata']['properties_analyzed'] = max(
        results['metadata']['properties_analyzed'], default=0
    )

    return results


def generate_summary_section(alerts_data: Dict[str, Any]) -> str:
    """
    Generate summary cards showing alert counts by detector type.
    [R9]: Priority-based summary for quick scanning

    Returns:
        HTML string for summary section
    """
    disaster_count = len(alerts_data['disasters'])
    spam_count = len(alerts_data['spam'])
    record_count = len(alerts_data['records'])
    trend_count = len(alerts_data['trends'])

    return f"""
    <table width="100%" style="margin: 30px 0;" cellpadding="0" cellspacing="0">
        <tr>
            <td width="25%" align="center" style="padding: 20px; background: #ffebee; border-radius: 8px;">
                <div style="color: {EMAIL_STYLES['danger_color']}; font-size: 36px; font-weight: 700;">{disaster_count}</div>
                <div style="color: {STM_COLORS['MARKETING']}; font-size: 12px; text-transform: uppercase;">DISASTERS (P0)</div>
            </td>
            <td width="25%" align="center" style="padding: 20px; background: #fff8e1; border-radius: 8px;">
                <div style="color: {EMAIL_STYLES['warning_color']}; font-size: 36px; font-weight: 700;">{spam_count}</div>
                <div style="color: {STM_COLORS['MARKETING']}; font-size: 12px; text-transform: uppercase;">SPAM (P1)</div>
            </td>
            <td width="25%" align="center" style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <div style="color: {STM_COLORS['SINGLE']}; font-size: 36px; font-weight: 700;">{record_count}</div>
                <div style="color: {STM_COLORS['MARKETING']}; font-size: 12px; text-transform: uppercase;">RECORDS</div>
            </td>
            <td width="25%" align="center" style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <div style="color: {STM_COLORS['SINGLE']}; font-size: 36px; font-weight: 700;">{trend_count}</div>
                <div style="color: {STM_COLORS['MARKETING']}; font-size: 12px; text-transform: uppercase;">TRENDS</div>
            </td>
        </tr>
    </table>
    """


def generate_disaster_section(disasters: List[Dict]) -> str:
    """
    Generate P0 disaster alert section with red styling.
    [R9]: Critical alerts first for AM visibility
    """
    if not disasters:
        return ""

    cards_html = ""
    for alert in disasters[:5]:  # Top 5 disasters only
        property_id = alert.get('property_id', 'Unknown')
        client_name = alert.get('client_name', property_id)
        disaster_type = alert.get('disaster_type', 'Unknown')
        metric = alert.get('metric', 'N/A')
        current_value = alert.get('current_value', 0)
        baseline = alert.get('baseline_value', 0)

        cards_html += f"""
        <div style="background: #ffebee; border-left: 4px solid {EMAIL_STYLES['danger_color']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{client_name}</strong>
                <span style="background: {EMAIL_STYLES['danger_color']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P0 - {disaster_type.upper()}</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Metric:</strong> {metric} |
                <strong>Current:</strong> {current_value} |
                <strong>Expected:</strong> {baseline}
            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom: 30px;">
        <h2 style="color: {EMAIL_STYLES['danger_color']}; font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee;">
            🚨 Critical Disasters (P0) - Immediate Action Required
        </h2>
        {cards_html}
    </div>
    """


def generate_spam_section(spam_alerts: List[Dict]) -> str:
    """
    Generate spam alert section with yellow styling.
    [R9]: Quality signal alerts for bot traffic
    """
    if not spam_alerts:
        return ""

    cards_html = ""
    for alert in spam_alerts[:10]:  # Top 10 spam alerts
        property_id = alert.get('property_id', 'Unknown')
        client_name = alert.get('client_name', property_id)
        dimension = alert.get('dimension', 'overall')
        segment_value = alert.get('segment_value', '')
        metric = alert.get('metric', 'sessions')
        z_score = alert.get('z_score', 0)
        bounce_rate = alert.get('bounce_rate', 0)
        avg_duration = alert.get('avg_session_duration', 0)

        segment_display = f" ({segment_value})" if segment_value else ""

        cards_html += f"""
        <div style="background: #fff8e1; border-left: 4px solid {EMAIL_STYLES['warning_color']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{client_name}{segment_display}</strong>
                <span style="background: {EMAIL_STYLES['warning_color']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P1 - SPAM</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Dimension:</strong> {dimension} |
                <strong>Z-Score:</strong> {z_score:.2f} |
                <strong>Bounce:</strong> {bounce_rate:.1f}% |
                <strong>Duration:</strong> {avg_duration:.0f}s
            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom: 30px;">
        <h2 style="color: {EMAIL_STYLES['warning_color']}; font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee;">
            ⚠️ Spam Detected (P1) - Quality Issues
        </h2>
        {cards_html}
    </div>
    """


def generate_record_section(records: List[Dict]) -> str:
    """
    Generate record alerts section (90-day highs/lows).
    [R9]: Mixed priority P1-P3 records
    """
    if not records:
        return ""

    # Separate highs and lows
    record_lows = [r for r in records if r.get('record_type') == 'low']
    record_highs = [r for r in records if r.get('record_type') == 'high']

    cards_html = ""

    # Show lows first (P1 priority)
    for alert in record_lows[:5]:
        property_id = alert.get('property_id', 'Unknown')
        domain = alert.get('domain', property_id)
        dimension = alert.get('dimension', 'overall')
        dimension_value = alert.get('dimension_value', '')
        metric = alert.get('metric', 'sessions')
        current_value = alert.get('value', 0)
        previous_record = alert.get('previous_record', 0)
        decline = alert.get('decline', 0)

        segment_display = f" ({dimension_value})" if dimension_value else ""

        cards_html += f"""
        <div style="background: #ffebee; border-left: 4px solid {EMAIL_STYLES['danger_color']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{domain}{segment_display}</strong>
                <span style="background: {EMAIL_STYLES['danger_color']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P1 - RECORD LOW ⚠️</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Metric:</strong> {metric} ({dimension}) |
                <strong>Current:</strong> {current_value} |
                <strong>Previous Record:</strong> {previous_record} |
                <strong>Decline:</strong> {decline:.1f}%
            </div>
        </div>
        """

    # Then highs (P3 good news)
    for alert in record_highs[:5]:
        property_id = alert.get('property_id', 'Unknown')
        domain = alert.get('domain', property_id)
        dimension = alert.get('dimension', 'overall')
        dimension_value = alert.get('dimension_value', '')
        metric = alert.get('metric', 'sessions')
        current_value = alert.get('value', 0)
        previous_record = alert.get('previous_record', 0)
        increase = alert.get('increase', 0)

        segment_display = f" ({dimension_value})" if dimension_value else ""

        cards_html += f"""
        <div style="background: #f1f8f4; border-left: 4px solid {STM_COLORS['THROW']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{domain}{segment_display}</strong>
                <span style="background: {STM_COLORS['THROW']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P3 - RECORD HIGH 🏆</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Metric:</strong> {metric} ({dimension}) |
                <strong>Current:</strong> {current_value} |
                <strong>Previous Record:</strong> {previous_record} |
                <strong>Increase:</strong> {increase:.1f}%
            </div>
        </div>
        """

    if not cards_html:
        return ""

    return f"""
    <div style="margin-bottom: 30px;">
        <h2 style="color: {STM_COLORS['SINGLE']}; font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee;">
            📊 90-Day Records
        </h2>
        {cards_html}
    </div>
    """


def generate_trend_section(trends: List[Dict]) -> str:
    """
    Generate trend alerts section (30-day vs 180-day comparison).
    [R9]: Directional change indicators (P2-P3)
    """
    if not trends:
        return ""

    # Separate downward (P2) and upward (P3) trends
    downward_trends = [t for t in trends if t.get('direction') == 'down']
    upward_trends = [t for t in trends if t.get('direction') == 'up']

    cards_html = ""

    # Show downward trends first (P2 priority)
    for alert in downward_trends[:5]:
        property_id = alert.get('property_id', 'Unknown')
        client_name = alert.get('client_name', property_id)
        dimension = alert.get('dimension', 'overall')
        metric = alert.get('metric', 'sessions')
        percent_change = alert.get('percent_change', 0)
        recent_avg = alert.get('recent_avg', 0)
        historical_avg = alert.get('historical_avg', 0)

        cards_html += f"""
        <div style="background: #fff8e1; border-left: 4px solid {EMAIL_STYLES['warning_color']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{client_name}</strong>
                <span style="background: {EMAIL_STYLES['warning_color']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P2 - DOWNWARD TREND ↘️</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Metric:</strong> {metric} ({dimension}) |
                <strong>Change:</strong> {percent_change:.1f}% |
                <strong>30-day avg:</strong> {recent_avg:.0f} |
                <strong>180-day avg:</strong> {historical_avg:.0f}
            </div>
        </div>
        """

    # Then upward trends (P3 good news)
    for alert in upward_trends[:5]:
        property_id = alert.get('property_id', 'Unknown')
        client_name = alert.get('client_name', property_id)
        dimension = alert.get('dimension', 'overall')
        metric = alert.get('metric', 'sessions')
        percent_change = alert.get('percent_change', 0)
        recent_avg = alert.get('recent_avg', 0)
        historical_avg = alert.get('historical_avg', 0)

        cards_html += f"""
        <div style="background: #f1f8f4; border-left: 4px solid {STM_COLORS['THROW']}; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <strong style="color: #24292E; font-size: 16px;">{client_name}</strong>
                <span style="background: {STM_COLORS['THROW']}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">P3 - UPWARD TREND ↗️</span>
            </div>
            <div style="color: {STM_COLORS['MARKETING']}; font-size: 14px;">
                <strong>Metric:</strong> {metric} ({dimension}) |
                <strong>Change:</strong> +{percent_change:.1f}% |
                <strong>30-day avg:</strong> {recent_avg:.0f} |
                <strong>180-day avg:</strong> {historical_avg:.0f}
            </div>
        </div>
        """

    if not cards_html:
        return ""

    return f"""
    <div style="margin-bottom: 30px;">
        <h2 style="color: {STM_COLORS['SINGLE']}; font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #eee;">
            📈 Trend Analysis (30-day vs 180-day)
        </h2>
        {cards_html}
    </div>
    """


def generate_html_email(alerts_data: Dict[str, Any]) -> str:
    """
    Generate complete HTML email digest with STM branding.
    [R9]: Consolidated email template with all detector sections

    Returns:
        Complete HTML email string
    """
    summary_html = generate_summary_section(alerts_data)
    disaster_html = generate_disaster_section(alerts_data['disasters'])
    spam_html = generate_spam_section(alerts_data['spam'])
    record_html = generate_record_section(alerts_data['records'])
    trend_html = generate_trend_section(alerts_data['trends'])

    # All clear message if no alerts
    if alerts_data['metadata']['total_alerts'] == 0:
        content_html = f"""
        <div style="text-align: center; padding: 60px 40px;">
            <div style="font-size: 64px; margin-bottom: 20px;">✅</div>
            <h2 style="color: {STM_COLORS['THROW']}; font-size: 24px; margin: 0 0 10px 0;">All Clear</h2>
            <p style="color: {STM_COLORS['MARKETING']}; font-size: 16px;">
                No anomalies detected across {alerts_data['metadata']['properties_analyzed']} properties.
                SCOUT is keeping watch.
            </p>
        </div>
        """
    else:
        content_html = f"""
        <p style="color: #24292E; font-size: 16px; line-height: 1.6;">
            Good morning,<br><br>
            SCOUT completed overnight reconnaissance across <strong>{alerts_data['metadata']['properties_analyzed']} properties</strong>.
            Here's what needs attention:
        </p>
        {summary_html}
        {disaster_html}
        {spam_html}
        {record_html}
        {trend_html}
        """

    now = datetime.now()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCOUT Daily Report - {now.strftime('%B %d, %Y')}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5;">
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table cellpadding="0" cellspacing="0" border="0" width="600" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

                    <!-- Header with STM Blue -->
                    <tr>
                        <td style="background-color: {EMAIL_STYLES['header_bg']}; padding: 40px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: {EMAIL_STYLES['header_text']}; font-size: 32px; text-align: center; font-weight: 600;">SCOUT</h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px; text-align: center;">Daily Reconnaissance Report</p>
                            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 12px; text-align: center;">{now.strftime('%A, %B %d, %Y')}</p>
                        </td>
                    </tr>

                    <!-- Gradient Bar (Scout Badge) -->
                    <tr>
                        <td style="background: linear-gradient(90deg, {STM_COLORS['THROW']} 0%, {EMAIL_STYLES['warning_color']} 50%, {EMAIL_STYLES['danger_color']} 100%); height: 4px;"></td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {content_html}
                        </td>
                    </tr>

                    <!-- Footer with STM Gray -->
                    <tr>
                        <td style="padding: 30px; background: {EMAIL_STYLES['background_color']}; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 10px 0; color: {STM_COLORS['MARKETING']}; font-size: 12px; text-align: center;">
                                <strong>SCOUT</strong> - Statistical Client Observation & Unified Tracking
                            </p>
                            <p style="margin: 0 0 10px 0; color: {STM_COLORS['MARKETING']}; font-size: 11px; text-align: center;">
                                Always watching. Always ready.
                            </p>
                            <p style="margin: 0; color: {STM_COLORS['MARKETING']}; font-size: 11px; text-align: center;">
                                Single Throw Marketing | Generated: {now.strftime('%I:%M %p ET')}
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


def main():
    """
    Main execution: Load alerts, generate email, save preview.
    [R9]: Email digest generation workflow
    """
    print("[R9] SCOUT Email Digest Generator")
    print("=" * 60)

    # Load all detector alerts
    print("\n1. Loading detector alerts...")
    alerts_data = load_detector_alerts()
    print(f"   - Disasters: {len(alerts_data['disasters'])}")
    print(f"   - Spam: {len(alerts_data['spam'])}")
    print(f"   - Records: {len(alerts_data['records'])}")
    print(f"   - Trends: {len(alerts_data['trends'])}")
    print(f"   - Total alerts: {alerts_data['metadata']['total_alerts']}")

    # Generate HTML email
    print("\n2. Generating HTML email digest...")
    html_email = generate_html_email(alerts_data)

    # Save preview HTML
    preview_path = Path(__file__).parent.parent / "data" / "scout_daily_digest_preview.html"
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(html_email)
    print(f"   ✅ Preview saved: {preview_path}")

    # Save email metadata for SendGrid
    email_metadata = {
        'generated_at': alerts_data['metadata']['generated_at'],
        'properties_analyzed': alerts_data['metadata']['properties_analyzed'],
        'total_alerts': alerts_data['metadata']['total_alerts'],
        'alert_counts': {
            'disasters': len(alerts_data['disasters']),
            'spam': len(alerts_data['spam']),
            'records': len(alerts_data['records']),
            'trends': len(alerts_data['trends'])
        },
        'ready_for_sendgrid': True
    }

    metadata_path = Path(__file__).parent.parent / "data" / "scout_email_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(email_metadata, f, indent=2)
    print(f"   ✅ Metadata saved: {metadata_path}")

    print("\n3. Email digest generation complete!")
    print(f"   - Open preview in browser: file://{preview_path.absolute()}")
    print(f"   - Next step: SendGrid API integration")


if __name__ == "__main__":
    main()
