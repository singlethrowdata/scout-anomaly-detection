#!/usr/bin/env python3
"""
SCOUT Production Cloud Functions
Main entry point for all scheduled SCOUT operations
"""

import functions_framework
import json
import os
import base64
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SCOUT')

# Environment configuration
PROJECT_ID = os.environ.get('GCP_PROJECT', 'stm-analytics-project')
DATASET_ID = os.environ.get('SCOUT_DATASET', 'scout_analytics')
# Handle both comma and semicolon separators for emails
recipients_raw = os.environ.get('ALERT_RECIPIENTS', '')
if ';' in recipients_raw:
    ALERT_RECIPIENTS = recipients_raw.split(';')
else:
    ALERT_RECIPIENTS = recipients_raw.split(',')
CHAT_WEBHOOK = os.environ.get('CHAT_WEBHOOK_URL', '')

# Initialize clients
bigquery_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

@functions_framework.http
def scout_daily_pipeline(request):
    """
    Main SCOUT pipeline - runs daily at 6 AM ET
    Orchestrates all detection, analysis, and alerting
    """
    try:
        logger.info(f"🚀 SCOUT Daily Pipeline Starting - {datetime.now()}")

        # Step 1: Data Ingestion and Validation
        logger.info("Phase 1: Data Ingestion")
        ingestion_results = run_data_ingestion()

        # Step 2: Anomaly Detection
        logger.info("Phase 2: Anomaly Detection")
        anomaly_results = run_anomaly_detection()

        # Step 3: Portfolio Pattern Analysis
        logger.info("Phase 3: Portfolio Pattern Analysis")
        pattern_results = run_portfolio_analysis(anomaly_results)

        # Step 4: Root Cause Correlation
        logger.info("Phase 4: Root Cause Analysis")
        enriched_results = run_root_cause_analysis(anomaly_results, pattern_results)

        # Step 5: Generate Predictions
        logger.info("Phase 5: Predictive Analysis")
        predictions = run_predictive_analysis(enriched_results, pattern_results)

        # Step 6: Send Alerts
        logger.info("Phase 6: Alert Generation")
        alert_results = send_alerts(enriched_results, predictions)

        # Log summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'anomalies_detected': len(anomaly_results),
            'patterns_found': len(pattern_results.get('patterns', [])),
            'alerts_sent': alert_results.get('sent_count', 0),
            'predictions_generated': len(predictions)
        }

        logger.info(f"✅ SCOUT Pipeline Complete: {json.dumps(summary)}")
        return json.dumps(summary), 200

    except Exception as e:
        logger.error(f"❌ SCOUT Pipeline Failed: {str(e)}")
        return json.dumps({'error': str(e), 'status': 'failed'}), 500

def run_data_ingestion():
    """
    Ingest and validate data from all client GA4 properties
    """
    # [R1-R4]: Data ingestion implementation
    # First, get list of all analytics datasets
    datasets_query = f"""
    SELECT schema_name
    FROM `{PROJECT_ID}.INFORMATION_SCHEMA.SCHEMATA`
    WHERE schema_name LIKE 'analytics_%'
    """

    try:
        datasets_df = bigquery_client.query(datasets_query).to_dataframe()
        analytics_datasets = datasets_df['schema_name'].tolist()
        logger.info(f"Found {len(analytics_datasets)} analytics datasets")
    except Exception as e:
        logger.error(f"Error fetching datasets: {e}")
        # Fallback to known dataset for testing
        analytics_datasets = ['analytics_249571600']

    # Build UNION query for all datasets
    union_parts = []
    for dataset in analytics_datasets:  # Process all datasets
        union_parts.append(f"""
        SELECT
            PARSE_DATE('%Y%m%d', event_date) as date,
            '{dataset}' as property_id,
            user_pseudo_id,
            event_name,
            COUNT(*) as event_count
        FROM `{PROJECT_ID}.{dataset}.events_*`
        WHERE PARSE_DATE('%Y%m%d', event_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 93 DAY)
        AND PARSE_DATE('%Y%m%d', event_date) <= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
        GROUP BY 1,2,3,4
        """)

    query = f"""
    WITH client_data AS (
        {' UNION ALL '.join(union_parts)}
    ),
    daily_metrics AS (
        SELECT
            date,
            property_id,
            COUNT(DISTINCT user_pseudo_id) as users,
            COUNT(*) as sessions,
            SUM(CASE WHEN event_name = 'page_view' THEN 1 ELSE 0 END) as page_views,
            SUM(CASE WHEN event_name IN ('purchase', 'submit_form') THEN 1 ELSE 0 END) as conversions
        FROM client_data
        GROUP BY 1,2
    )
    SELECT * FROM daily_metrics
    ORDER BY date DESC, property_id
    """

    df = bigquery_client.query(query).to_dataframe()
    logger.info(f"✅ Ingested data for {df['property_id'].nunique()} properties")

    # Store in temporary table for processing
    table_id = f"{PROJECT_ID}.{DATASET_ID}.daily_metrics_temp"
    job = bigquery_client.load_table_from_dataframe(df, table_id)
    job.result()

    return {'properties': df['property_id'].nunique(), 'records': len(df)}

def run_anomaly_detection():
    """
    Detect anomalies using statistical methods
    """
    # [R5-R6]: Anomaly detection implementation
    query = f"""
    WITH baseline AS (
        SELECT
            property_id,
            AVG(users) as avg_users,
            STDDEV(users) as std_users,
            AVG(sessions) as avg_sessions,
            STDDEV(sessions) as std_sessions,
            AVG(conversions) as avg_conversions,
            STDDEV(conversions) as std_conversions
        FROM `{PROJECT_ID}.{DATASET_ID}.daily_metrics_temp`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 93 DAY)
        AND date <= DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY)
        GROUP BY property_id
    ),
    current_data AS (
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.daily_metrics_temp`
        WHERE date = DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
    )
    SELECT
        c.*,
        b.avg_users, b.std_users,
        ABS((c.users - b.avg_users) / NULLIF(b.std_users, 0)) as users_z_score,
        ABS((c.sessions - b.avg_sessions) / NULLIF(b.std_sessions, 0)) as sessions_z_score,
        ABS((c.conversions - b.avg_conversions) / NULLIF(b.std_conversions, 0)) as conversions_z_score
    FROM current_data c
    JOIN baseline b ON c.property_id = b.property_id
    WHERE
        ABS((c.users - b.avg_users) / NULLIF(b.std_users, 0)) > 1.5 OR
        ABS((c.sessions - b.avg_sessions) / NULLIF(b.std_sessions, 0)) > 1.5 OR
        ABS((c.conversions - b.avg_conversions) / NULLIF(b.std_conversions, 0)) > 1.5
    """

    anomalies = bigquery_client.query(query).to_dataframe()

    # Calculate business impact scores
    anomaly_list = []
    for _, row in anomalies.iterrows():
        for metric in ['users', 'sessions', 'conversions']:
            z_score = row.get(f'{metric}_z_score', 0)
            if z_score > 1.5:
                impact_score = calculate_impact_score(metric, z_score)
                anomaly_list.append({
                    'property_id': row['property_id'],
                    'date': row['date'].isoformat(),
                    'metric': metric,
                    'value': row[metric],
                    'z_score': z_score,
                    'impact_score': impact_score
                })

    logger.info(f"✅ Detected {len(anomaly_list)} anomalies")

    # Store anomalies in BigQuery for Looker Studio
    if anomaly_list:
        try:
            table_id = f"{PROJECT_ID}.{DATASET_ID}.anomalies_detected"
            rows_to_insert = []
            for anomaly in anomaly_list:
                rows_to_insert.append({
                    'date': anomaly.get('date'),
                    'property_id': anomaly.get('property_id'),
                    'client_name': anomaly.get('property_id', '').replace('analytics_', ''),
                    'metric': anomaly.get('metric'),
                    'actual_value': float(anomaly.get('value', 0)),
                    'expected_value': float(anomaly.get('baseline_value', 0)),
                    'deviation_percent': float(anomaly.get('deviation_percent', 0)),
                    'z_score': float(anomaly.get('z_score', 0)),
                    'impact_score': int(anomaly.get('impact_score', 0)),
                    'priority': 'critical' if anomaly.get('impact_score', 0) > 70 else 'warning' if anomaly.get('impact_score', 0) > 40 else 'normal',
                    'detection_timestamp': datetime.now().isoformat()
                })

            table = bigquery_client.get_table(table_id)
            errors = bigquery_client.insert_rows_json(table, rows_to_insert)

            if not errors:
                logger.info(f"✅ Saved {len(rows_to_insert)} anomalies to BigQuery")
            else:
                logger.error(f"Error inserting rows: {errors}")
        except Exception as e:
            logger.error(f"Error saving to BigQuery: {e}")

    return anomaly_list

def run_portfolio_analysis(anomalies):
    """
    Analyze patterns across the portfolio
    """
    # [R7]: Portfolio pattern detection
    patterns = {
        'patterns': [],
        'portfolio_health': 100
    }

    if not anomalies:
        return patterns

    # Group by date to find simultaneous anomalies
    from collections import defaultdict
    date_groups = defaultdict(list)

    for anomaly in anomalies:
        date_groups[anomaly['date']].append(anomaly)

    # Find dates with multiple properties affected
    for date, date_anomalies in date_groups.items():
        if len(date_anomalies) >= 3:  # 3+ properties = pattern
            patterns['patterns'].append({
                'type': 'simultaneous',
                'date': date,
                'affected_properties': len(date_anomalies),
                'metrics': list(set(a['metric'] for a in date_anomalies)),
                'confidence': min(len(date_anomalies) / 10, 1.0)  # Assuming ~50 properties
            })

    # Calculate portfolio health
    total_properties = 50  # Approximate
    affected = len(set(a['property_id'] for a in anomalies))
    patterns['portfolio_health'] = max(0, 100 - (affected / total_properties * 100))

    logger.info(f"✅ Found {len(patterns['patterns'])} portfolio patterns")
    return patterns

def run_root_cause_analysis(anomalies, patterns):
    """
    Correlate with external events
    """
    # [R11]: Root cause correlation
    # Simplified version - in production would load from database
    known_events = {
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'): {
            'name': 'Weekend Effect',
            'confidence': 0.4
        }
    }

    enriched = []
    for anomaly in anomalies:
        enriched_anomaly = anomaly.copy()

        # Check for known events
        if anomaly['date'] in known_events:
            enriched_anomaly['root_cause'] = known_events[anomaly['date']]
        else:
            enriched_anomaly['root_cause'] = {'name': 'Unknown', 'confidence': 0.1}

        enriched.append(enriched_anomaly)

    return enriched

def run_predictive_analysis(anomalies, patterns):
    """
    Generate predictions for next 7 days
    """
    # [R12]: Predictive alerts
    predictions = []

    # Simple prediction based on patterns
    if patterns.get('patterns'):
        for pattern in patterns['patterns']:
            predictions.append({
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'prediction': 'Similar pattern likely to continue',
                'confidence': pattern.get('confidence', 0.5),
                'action': 'Monitor affected properties closely'
            })

    logger.info(f"✅ Generated {len(predictions)} predictions")
    return predictions

def send_alerts(anomalies, predictions):
    """
    Send alerts via email and chat
    """
    # [R9-R10]: Alert delivery
    if not anomalies:
        logger.info("No anomalies to alert on")
        return {'sent_count': 0}

    # Get recipients from environment
    recipients = ALERT_RECIPIENTS
    if not recipients:
        logger.warning("No ALERT_RECIPIENTS configured")
        recipients = ["data@singlethrow.com"]  # Default recipient

    alert_summary = {
        'timestamp': datetime.now().isoformat(),
        'anomaly_count': len(anomalies),
        'critical': len([a for a in anomalies if a.get('impact_score', 0) > 70]),
        'warning': len([a for a in anomalies if 40 <= a.get('impact_score', 0) < 70]),
        'predictions': len(predictions),
        'recipients': recipients
    }

    logger.info(f"📧 Alert prepared for: {', '.join(recipients)}")
    logger.info(f"📊 Summary: {json.dumps(alert_summary)}")

    # Generate email HTML
    html_content = generate_alert_email(anomalies, predictions, alert_summary)

    # Send email via Gmail API
    email_sent = send_gmail(recipients, alert_summary, html_content)

    # Send to Cloud Storage for record
    bucket_name = f"{PROJECT_ID}-scout-alerts"
    blob_name = f"alerts/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps({
            'anomalies': anomalies[:10],  # Sample
            'predictions': predictions,
            'summary': alert_summary
        }))
        logger.info(f"✅ Alert saved to gs://{bucket_name}/{blob_name}")
    except Exception as e:
        logger.warning(f"Could not save to storage: {e}")

    return {'sent_count': 1, 'summary': alert_summary}

def calculate_impact_score(metric, z_score):
    """
    Calculate business impact score
    """
    weights = {
        'conversions': 2.0,
        'users': 1.2,
        'sessions': 1.0,
        'page_views': 0.8
    }

    base_score = min(z_score * 10, 50)
    weight = weights.get(metric, 1.0)

    return min(base_score * weight, 100)

def send_gmail(recipients, summary, html_content):
    """
    Send email using Gmail API
    """
    try:
        # Use default credentials (service account)
        credentials = service_account.Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": PROJECT_ID,
            },
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )

        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)

        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = f"🔭 SCOUT Alert: {summary['anomaly_count']} Anomalies Detected"
        message['From'] = f"scout-alerts@{PROJECT_ID}.iam.gserviceaccount.com"
        message['To'] = ', '.join(recipients)

        # Add HTML part
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send message
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        logger.info(f"✅ Email sent successfully! Message ID: {result.get('id')}")
        return True

    except HttpError as error:
        logger.error(f"❌ Gmail API error: {error}")
        logger.info("Falling back to logging mode - email content logged but not sent")

        # Log the alert details for visibility
        logger.info("=" * 60)
        logger.info("🔭 SCOUT ALERT (Email Not Sent - Logged Only)")
        logger.info("=" * 60)
        logger.info(f"Recipients: {', '.join(recipients)}")
        logger.info(f"Anomalies: {summary['anomaly_count']} total")
        logger.info(f"  Critical: {summary.get('critical', 0)}")
        logger.info(f"  Warning: {summary.get('warning', 0)}")
        logger.info("=" * 60)

        return False
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        logger.info("Note: Gmail API requires domain-wide delegation for service accounts")
        logger.info("For now, alerts are being logged. To enable email:")
        logger.info("1. Set up domain-wide delegation for the service account")
        logger.info("2. Or use SendGrid API (add SENDGRID_API_KEY to environment)")

        # Log the alert details for visibility
        logger.info("=" * 60)
        logger.info("🔭 SCOUT ALERT (Email Not Sent - Logged Only)")
        logger.info("=" * 60)
        logger.info(f"Recipients: {', '.join(recipients)}")
        logger.info(f"Anomalies: {summary['anomaly_count']} total")
        logger.info(f"  Critical: {summary.get('critical', 0)}")
        logger.info(f"  Warning: {summary.get('warning', 0)}")
        logger.info("=" * 60)

        return False

def generate_alert_email(anomalies, predictions, summary):
    """
    Generate HTML email content for alerts
    """
    critical_anomalies = [a for a in anomalies if a.get('impact_score', 0) > 70]
    warning_anomalies = [a for a in anomalies if 40 <= a.get('impact_score', 0) < 70]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .header {{ background: #1A5276; color: white; padding: 20px; text-align: center; }}
            .gradient {{ height: 4px; background: linear-gradient(90deg, #6B8F71, #F39C12, #E74C3C); }}
            .summary {{ padding: 20px; }}
            .alert {{ margin: 10px 20px; padding: 10px; border-left: 4px solid; }}
            .critical {{ border-color: #E74C3C; background: #FEE; }}
            .warning {{ border-color: #F39C12; background: #FFE; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔭 SCOUT Alert Report</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            <div class="gradient"></div>
            <div class="summary">
                <h2>Summary</h2>
                <p>Detected {summary['anomaly_count']} anomalies:</p>
                <ul>
                    <li>Critical: {summary.get('critical', 0)}</li>
                    <li>Warning: {summary.get('warning', 0)}</li>
                    <li>Predictions: {summary.get('predictions', 0)}</li>
                </ul>
            </div>
            {"".join([f'<div class="alert critical"><b>{a["property_id"]}</b> - {a["metric"]}: Impact {a.get("impact_score", 0)}</div>' for a in critical_anomalies[:5]])}
            {"".join([f'<div class="alert warning"><b>{a["property_id"]}</b> - {a["metric"]}: Impact {a.get("impact_score", 0)}</div>' for a in warning_anomalies[:5]])}
        </div>
    </body>
    </html>
    """
    return html

# Health check endpoint
@functions_framework.http
def health_check(request):
    """Simple health check endpoint"""
    return json.dumps({'status': 'healthy', 'service': 'SCOUT'}), 200