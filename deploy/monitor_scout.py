#!/usr/bin/env python3
"""
SCOUT Operations Monitoring Dashboard
Simple CLI tool to monitor SCOUT pipeline health and costs
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud import logging
from google.cloud import monitoring_v3
import argparse
from typing import Dict, List

class SCOUTMonitor:
    """Monitor SCOUT operations"""

    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.environ.get('GCP_PROJECT', 'stm-analytics-project')
        self.bq_client = bigquery.Client(project=self.project_id)
        self.logging_client = logging.Client(project=self.project_id)

    def check_pipeline_status(self) -> Dict:
        """Check if pipeline ran successfully today"""
        # [Monitoring]: Pipeline health check
        query = f"""
        SELECT
            MAX(detection_timestamp) as last_run,
            COUNT(*) as anomalies_today,
            COUNT(DISTINCT property_id) as properties_analyzed,
            AVG(business_impact_score) as avg_impact
        FROM `{self.project_id}.scout_analytics.anomalies`
        WHERE DATE(detection_timestamp) = CURRENT_DATE()
        """

        try:
            result = self.bq_client.query(query).result()
            for row in result:
                last_run = row.last_run
                if last_run:
                    hours_ago = (datetime.now() - last_run.replace(tzinfo=None)).total_seconds() / 3600
                    status = "✅ HEALTHY" if hours_ago < 24 else "⚠️ DELAYED"
                else:
                    status = "❌ NOT RUN"
                    hours_ago = None

                return {
                    'status': status,
                    'last_run': last_run.isoformat() if last_run else "Never",
                    'hours_since_run': round(hours_ago, 1) if hours_ago else None,
                    'anomalies_detected': row.anomalies_today,
                    'properties_analyzed': row.properties_analyzed,
                    'avg_impact_score': round(row.avg_impact, 1) if row.avg_impact else 0
                }
        except Exception as e:
            return {
                'status': '❌ ERROR',
                'error': str(e)
            }

    def calculate_costs(self, days: int = 30) -> Dict:
        """Calculate BigQuery processing costs"""
        # [Monitoring]: Cost tracking
        query = f"""
        SELECT
            SUM(total_bytes_billed) / POW(10, 12) as tb_processed,
            COUNT(*) as query_count,
            SUM(total_slot_ms) / 1000 / 60 / 60 as slot_hours
        FROM `{self.project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE
            creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            AND statement_type = 'SELECT'
            AND user_email LIKE '%scout%'
        """

        try:
            result = self.bq_client.query(query).result()
            for row in result:
                # BigQuery pricing: $5 per TB
                cost_estimate = (row.tb_processed or 0) * 5

                return {
                    'period_days': days,
                    'tb_processed': round(row.tb_processed or 0, 3),
                    'queries_run': row.query_count or 0,
                    'estimated_cost_usd': round(cost_estimate, 2),
                    'daily_avg_cost': round(cost_estimate / days, 2)
                }
        except Exception as e:
            return {'error': str(e)}

    def get_alert_metrics(self, days: int = 7) -> Dict:
        """Get alert delivery metrics"""
        # [Monitoring]: Alert tracking
        query = f"""
        SELECT
            DATE(detection_timestamp) as date,
            priority,
            COUNT(*) as count,
            COUNT(DISTINCT property_id) as unique_properties
        FROM `{self.project_id}.scout_analytics.anomalies`
        WHERE
            DATE(detection_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
            AND alert_sent = TRUE
        GROUP BY date, priority
        ORDER BY date DESC, priority
        """

        try:
            df = self.bq_client.query(query).to_dataframe()

            summary = {
                'total_alerts': len(df),
                'critical_alerts': df[df['priority'] == 'critical']['count'].sum() if not df.empty else 0,
                'warning_alerts': df[df['priority'] == 'warning']['count'].sum() if not df.empty else 0,
                'by_date': {}
            }

            for date in df['date'].unique():
                date_str = date.strftime('%Y-%m-%d')
                date_data = df[df['date'] == date]
                summary['by_date'][date_str] = {
                    'total': date_data['count'].sum(),
                    'critical': date_data[date_data['priority'] == 'critical']['count'].sum() if not date_data.empty else 0
                }

            return summary
        except Exception as e:
            return {'error': str(e)}

    def check_error_logs(self, hours: int = 24) -> List[Dict]:
        """Check for recent errors in Cloud Functions"""
        # [Monitoring]: Error detection
        errors = []

        # Set up the filter
        filter_str = f"""
        resource.type="cloud_function"
        resource.labels.function_name=~"scout.*"
        severity >= ERROR
        timestamp >= "{(datetime.now() - timedelta(hours=hours)).isoformat()}Z"
        """

        try:
            entries = self.logging_client.list_entries(filter_=filter_str, max_results=10)

            for entry in entries:
                errors.append({
                    'timestamp': entry.timestamp.isoformat(),
                    'severity': entry.severity,
                    'message': entry.payload.get('message', str(entry.payload))[:200],
                    'function': entry.resource.labels.get('function_name', 'unknown')
                })

            return errors
        except Exception as e:
            return [{'error': str(e)}]

    def generate_dashboard(self) -> None:
        """Generate complete monitoring dashboard"""
        print("\n" + "="*60)
        print("🔭 SCOUT OPERATIONS DASHBOARD")
        print("="*60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Pipeline Status
        print("\n📊 PIPELINE STATUS")
        print("-"*40)
        status = self.check_pipeline_status()
        print(f"Status: {status.get('status', 'Unknown')}")
        if status.get('last_run'):
            print(f"Last Run: {status['last_run']}")
            if status.get('hours_since_run'):
                print(f"Hours Ago: {status['hours_since_run']}")
            print(f"Anomalies Detected: {status.get('anomalies_detected', 0)}")
            print(f"Properties Analyzed: {status.get('properties_analyzed', 0)}")
            print(f"Avg Impact Score: {status.get('avg_impact_score', 0)}")

        # Cost Analysis
        print("\n💰 COST ANALYSIS (Last 30 Days)")
        print("-"*40)
        costs = self.calculate_costs(30)
        if 'error' not in costs:
            print(f"Data Processed: {costs['tb_processed']} TB")
            print(f"Queries Run: {costs['queries_run']}")
            print(f"Estimated Cost: ${costs['estimated_cost_usd']}")
            print(f"Daily Average: ${costs['daily_avg_cost']}")

            # Check against budget
            monthly_budget = 100
            if costs['estimated_cost_usd'] > monthly_budget:
                print(f"⚠️ WARNING: Over budget! (Budget: ${monthly_budget})")
            else:
                print(f"✅ Within budget (Budget: ${monthly_budget})")
        else:
            print(f"Error: {costs['error']}")

        # Alert Metrics
        print("\n📧 ALERT METRICS (Last 7 Days)")
        print("-"*40)
        alerts = self.get_alert_metrics(7)
        if 'error' not in alerts:
            print(f"Total Alerts Sent: {alerts['total_alerts']}")
            print(f"Critical: {alerts['critical_alerts']}")
            print(f"Warning: {alerts['warning_alerts']}")

            if alerts['by_date']:
                print("\nDaily Breakdown:")
                for date, data in sorted(alerts['by_date'].items(), reverse=True)[:5]:
                    print(f"  {date}: {data['total']} alerts ({data['critical']} critical)")
        else:
            print(f"Error: {alerts['error']}")

        # Error Logs
        print("\n🚨 RECENT ERRORS (Last 24 Hours)")
        print("-"*40)
        errors = self.check_error_logs(24)
        if errors and 'error' not in errors[0]:
            if errors:
                for error in errors[:5]:
                    print(f"  [{error['severity']}] {error['timestamp'][:19]}")
                    print(f"    {error['message']}")
            else:
                print("✅ No errors found")
        elif errors and 'error' in errors[0]:
            print(f"Error checking logs: {errors[0]['error']}")
        else:
            print("✅ No errors found")

        # Health Summary
        print("\n🏥 HEALTH SUMMARY")
        print("-"*40)

        health_score = 100
        issues = []

        # Check pipeline status
        if status.get('status') and 'HEALTHY' not in status['status']:
            health_score -= 30
            issues.append("Pipeline not running properly")

        # Check costs
        if costs.get('estimated_cost_usd', 0) > 100:
            health_score -= 20
            issues.append("Over budget")

        # Check errors
        if errors and 'error' not in errors[0] and len(errors) > 0:
            health_score -= 10 * min(len(errors), 3)
            issues.append(f"{len(errors)} errors in last 24h")

        print(f"Overall Health Score: {health_score}/100")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("✅ All systems operational")

        print("\n" + "="*60)
        print("Use 'python monitor_scout.py --help' for more options")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Monitor SCOUT operations')
    parser.add_argument('--project', help='GCP project ID', default=None)
    parser.add_argument('--costs-only', action='store_true', help='Show only cost analysis')
    parser.add_argument('--alerts-only', action='store_true', help='Show only alert metrics')
    parser.add_argument('--errors-only', action='store_true', help='Show only recent errors')

    args = parser.parse_args()

    monitor = SCOUTMonitor(project_id=args.project)

    if args.costs_only:
        costs = monitor.calculate_costs(30)
        print(f"BigQuery Costs (30 days): ${costs.get('estimated_cost_usd', 0)}")
    elif args.alerts_only:
        alerts = monitor.get_alert_metrics(7)
        print(f"Alerts (7 days): {alerts.get('total_alerts', 0)} total")
    elif args.errors_only:
        errors = monitor.check_error_logs(24)
        print(f"Errors (24h): {len(errors)}")
    else:
        monitor.generate_dashboard()


if __name__ == "__main__":
    main()