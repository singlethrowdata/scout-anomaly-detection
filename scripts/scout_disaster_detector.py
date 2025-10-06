#!/usr/bin/env python3
"""
SCOUT Disaster Detector - P0 Critical Alert System
[R17]: Disaster detection for catastrophic failures
→ needs: clean-data
→ provides: disaster-alerts

Algorithm: Threshold-based comparison
BigQuery Window: DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY) to yesterday
Comparison: Yesterday vs 3-day average
Dimensions: Overall ONLY (site-wide failures)
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def detect_disaster_alerts(property_file: str) -> List[Dict]:
    """
    Detect catastrophic failures using threshold-based comparison.

    Triggers:
    - sessions < 10 (near-zero traffic)
    - conversions = 0 (tracking failure)
    - 90%+ traffic drop from baseline

    Args:
        property_file: Path to temp_property_*.json file with 3-day data

    Returns:
        List of disaster alerts (0-3 per property expected)
    """
    print(f'Processing: {property_file}')

    # Read UTF-8 encoded file (production clean files)
    with open(property_file, 'r', encoding='utf-8') as f:
        file_data = json.load(f)

    # Extract data from production clean format
    daily_overall = file_data['clean_dataset']
    metadata = file_data['client_metadata']
    property_id = metadata['property_id']
    domain = metadata.get('inferred_domain', '').replace('https://www.', '').replace('/', '')
    disaster_alerts = []

    # Process OVERALL metrics only (site-wide failures)
    # daily_overall = data.get('daily_overall', [])

    if len(daily_overall) < 2:
        print(f'  ⚠️  Insufficient data (need at least 2 days)')
        return disaster_alerts

    # Yesterday is the most recent day
    yesterday = daily_overall[-1]
    yesterday_date = yesterday['date']
    yesterday_sessions = int(yesterday.get('sessions', 0))
    yesterday_conversions = int(yesterday.get('conversions', 0))

    # Calculate 3-day average (excluding yesterday)
    baseline_days = daily_overall[:-1]
    baseline_sessions = [int(d.get('sessions', 0)) for d in baseline_days]
    avg_sessions = statistics.mean(baseline_sessions) if baseline_sessions else 0

    # Disaster Check 1: Near-zero traffic (sessions < 10)
    if yesterday_sessions < 10:
        disaster_alerts.append({
            'property_id': property_id,
            'domain': domain,
            'date': yesterday_date,
            'anomaly_type': 'disaster',
            'priority': 'P0',
            'disaster_type': 'near_zero_traffic',
            'metric': 'sessions',
            'value': yesterday_sessions,
            'threshold': 10,
            'baseline': round(avg_sessions, 2),
            'message': f'Site down: Only {yesterday_sessions} sessions detected',
            'action_required': 'ACT NOW - Check tracking code and site availability',
            'business_impact': 100,
            'detected_at': datetime.now().isoformat()
        })

    # Disaster Check 2: Tracking failure (conversions = 0)
    if yesterday_conversions == 0 and avg_sessions > 50:  # Only alert if site has meaningful traffic
        disaster_alerts.append({
            'property_id': property_id,
            'domain': domain,
            'date': yesterday_date,
            'anomaly_type': 'disaster',
            'priority': 'P0',
            'disaster_type': 'tracking_failure',
            'metric': 'conversions',
            'value': 0,
            'threshold': 1,
            'baseline': 'N/A',
            'message': 'Conversion tracking failure: 0 conversions detected',
            'action_required': 'ACT NOW - Verify GA4 event configuration',
            'business_impact': 100,
            'detected_at': datetime.now().isoformat()
        })

    # Disaster Check 3: 90%+ traffic drop
    if avg_sessions > 0:
        drop_percentage = ((avg_sessions - yesterday_sessions) / avg_sessions) * 100

        if drop_percentage >= 90:
            disaster_alerts.append({
                'property_id': property_id,
                'domain': domain,
                'date': yesterday_date,
                'anomaly_type': 'disaster',
                'priority': 'P0',
                'disaster_type': 'catastrophic_drop',
                'metric': 'sessions',
                'value': yesterday_sessions,
                'threshold': round(avg_sessions * 0.1, 2),  # 10% of average
                'baseline': round(avg_sessions, 2),
                'drop_percentage': round(drop_percentage, 2),
                'message': f'Catastrophic traffic drop: -{round(drop_percentage, 1)}%',
                'action_required': 'ACT NOW - Investigate site outage or tracking issue',
                'business_impact': 100,
                'detected_at': datetime.now().isoformat()
            })

    print(f'  🚨 Found {len(disaster_alerts)} disaster alerts')
    return disaster_alerts


def main():
    """Process all properties and generate disaster alert report."""
    all_alerts = []
    data_dir = Path('data')

    # Process temp_property_*.json files (3-day data with buffer)
    property_files = sorted(data_dir.glob('scout_production_clean_*.json'))

    if not property_files:
        print('❌ No property files found (looking for scout_production_clean_*.json)')
        print('   Run BigQuery export first to generate data files')
        return

    print(f'🔍 Processing {len(property_files)} properties for disaster detection...\n')

    for file_path in property_files:
        try:
            alerts = detect_disaster_alerts(str(file_path))
            all_alerts.extend(alerts)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'detector_type': 'disaster',
        'priority': 'P0',
        'properties_analyzed': len(property_files),
        'total_alerts': len(all_alerts),
        'disaster_types': ['near_zero_traffic', 'tracking_failure', 'catastrophic_drop'],
        'alerts': all_alerts
    }

    # Save report
    output_file = data_dir / 'scout_disaster_alerts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n✅ Disaster detection complete')
    print(f'📊 Generated {len(all_alerts)} P0 alerts')
    print(f'💾 Saved to: {output_file}')

    if all_alerts:
        print(f'\n🚨 CRITICAL DISASTERS DETECTED:')
        disaster_types = {}
        for alert in all_alerts:
            dtype = alert['disaster_type']
            disaster_types[dtype] = disaster_types.get(dtype, 0) + 1

        for dtype, count in disaster_types.items():
            print(f'  • {dtype}: {count} alerts')
    else:
        print(f'\n✅ No disasters detected (all properties healthy)')


if __name__ == '__main__':
    main()
