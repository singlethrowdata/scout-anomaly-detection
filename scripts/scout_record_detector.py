#!/usr/bin/env python3
"""
SCOUT Record Detector - P1-P3 Mixed Priority Alert System
[R19]: Record detection for all-time highs/lows
→ needs: historical-data-90day
→ provides: record-alerts

Algorithm: Historical max/min comparison
BigQuery Window: DATE_SUB(CURRENT_DATE(), INTERVAL 93 DAY) to yesterday
Comparison: Yesterday vs last 90 days
Dimensions: Overall, Landing Pages, Devices, Traffic Source
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def detect_record_alerts(property_file: str, min_sessions: int = 100) -> List[Dict]:
    """
    Detect 90-day record highs and lows.

    Args:
        property_file: Path to weekly_property_*.json file with 90-day data
        min_sessions: Minimum daily sessions to qualify (default: 100)

    Returns:
        List of record alerts for qualified segments
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
    record_alerts = []

    # Process OVERALL dimension
    # daily_overall = data.get('daily_overall', [])

    if len(daily_overall) >= 2:
        yesterday = daily_overall[-1]
        historical = daily_overall[:-1]

        yesterday_sessions = int(yesterday.get('sessions', 0))

        # Only process if meets minimum volume
        if yesterday_sessions >= min_sessions:
            sessions_history = [int(d.get('sessions', 0)) for d in historical]
            max_sessions = max(sessions_history)
            min_sessions_val = min(sessions_history)

            # Check for new high
            if yesterday_sessions > max_sessions:
                record_alerts.append({
                    'property_id': property_id,
                    'domain': domain,
                    'date': yesterday['date'],
                    'anomaly_type': 'record',
                    'priority': 'P3',  # Good news
                    'record_type': 'high',
                    'dimension': 'overall',
                    'dimension_value': 'site-wide',
                    'metric': 'sessions',
                    'value': yesterday_sessions,
                    'previous_record': max_sessions,
                    'improvement': round(((yesterday_sessions - max_sessions) / max_sessions) * 100, 2),
                    'message': f'🏆 New 90-day high: {yesterday_sessions} sessions (previous: {max_sessions})',
                    'action_required': 'Document what drove this success',
                    'business_impact': 75,
                    'detected_at': datetime.now().isoformat()
                })

            # Check for new low
            elif yesterday_sessions < min_sessions_val:
                record_alerts.append({
                    'property_id': property_id,
                    'domain': domain,
                    'date': yesterday['date'],
                    'anomaly_type': 'record',
                    'priority': 'P1',  # Bad news - worst ever
                    'record_type': 'low',
                    'dimension': 'overall',
                    'dimension_value': 'site-wide',
                    'metric': 'sessions',
                    'value': yesterday_sessions,
                    'previous_record': min_sessions_val,
                    'decline': round(((min_sessions_val - yesterday_sessions) / min_sessions_val) * 100, 2),
                    'message': f'⚠️ New 90-day low: {yesterday_sessions} sessions (previous low: {min_sessions_val})',
                    'action_required': 'Investigate cause of all-time low',
                    'business_impact': 100,
                    'detected_at': datetime.now().isoformat()
                })

    # Process DEVICE dimension
    device_segments = file_data.get('device_segments', [])
    if device_segments:
        device_data = {}
        for seg in device_segments:
            device = seg.get('device_category', '')
            if not device:
                continue
            if device not in device_data:
                device_data[device] = []
            device_data[device].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0))
            })

        for device, points in device_data.items():
            if len(points) < 2:
                continue

            yesterday = points[-1]
            historical = points[:-1]

            if yesterday['sessions'] >= min_sessions:
                sessions_history = [p['sessions'] for p in historical]
                max_val = max(sessions_history)
                min_val = min(sessions_history)

                if yesterday['sessions'] > max_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P3',
                        'record_type': 'high',
                        'dimension': 'device',
                        'dimension_value': device,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': max_val,
                        'improvement': round(((yesterday['sessions'] - max_val) / max_val) * 100, 2),
                        'message': f'🏆 {device} record high: {yesterday["sessions"]} sessions',
                        'action_required': f'Document {device} growth drivers',
                        'business_impact': 75,
                        'detected_at': datetime.now().isoformat()
                    })

                elif yesterday['sessions'] < min_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P1',
                        'record_type': 'low',
                        'dimension': 'device',
                        'dimension_value': device,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': min_val,
                        'decline': round(((min_val - yesterday['sessions']) / min_val) * 100, 2),
                        'message': f'⚠️ {device} record low: {yesterday["sessions"]} sessions',
                        'action_required': f'Investigate {device} decline',
                        'business_impact': 100,
                        'detected_at': datetime.now().isoformat()
                    })

    # Process TRAFFIC SOURCE dimension
    traffic_segments = file_data.get('traffic_segments', [])
    if traffic_segments:
        source_data = {}
        for seg in traffic_segments:
            source_medium = f"{seg.get('source', '')}/{seg.get('medium', '')}"
            if source_medium not in source_data:
                source_data[source_medium] = []
            source_data[source_medium].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0))
            })

        for source_medium, points in source_data.items():
            if len(points) < 2:
                continue

            yesterday = points[-1]
            historical = points[:-1]

            if yesterday['sessions'] >= min_sessions:
                sessions_history = [p['sessions'] for p in historical]
                max_val = max(sessions_history)
                min_val = min(sessions_history)

                if yesterday['sessions'] > max_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P3',
                        'record_type': 'high',
                        'dimension': 'traffic_source',
                        'dimension_value': source_medium,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': max_val,
                        'improvement': round(((yesterday['sessions'] - max_val) / max_val) * 100, 2),
                        'message': f'🏆 {source_medium} record high: {yesterday["sessions"]} sessions',
                        'action_required': f'Scale {source_medium} success',
                        'business_impact': 75,
                        'detected_at': datetime.now().isoformat()
                    })

                elif yesterday['sessions'] < min_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P1',
                        'record_type': 'low',
                        'dimension': 'traffic_source',
                        'dimension_value': source_medium,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': min_val,
                        'decline': round(((min_val - yesterday['sessions']) / min_val) * 100, 2),
                        'message': f'⚠️ {source_medium} record low: {yesterday["sessions"]} sessions',
                        'action_required': f'Fix {source_medium} traffic loss',
                        'business_impact': 100,
                        'detected_at': datetime.now().isoformat()
                    })

    # Process LANDING PAGE dimension
    page_segments = file_data.get('page_segments', [])
    if page_segments:
        page_data = {}
        for seg in page_segments:
            page_path = seg.get('landing_page', '')
            if not page_path:
                continue
            if page_path not in page_data:
                page_data[page_path] = []
            page_data[page_path].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0))
            })

        for page_path, points in page_data.items():
            if len(points) < 2:
                continue

            yesterday = points[-1]
            historical = points[:-1]

            if yesterday['sessions'] >= min_sessions:
                sessions_history = [p['sessions'] for p in historical]
                max_val = max(sessions_history)
                min_val = min(sessions_history)

                if yesterday['sessions'] > max_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P3',
                        'record_type': 'high',
                        'dimension': 'landing_page',
                        'dimension_value': page_path,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': max_val,
                        'improvement': round(((yesterday['sessions'] - max_val) / max_val) * 100, 2),
                        'message': f'🏆 {page_path} record high: {yesterday["sessions"]} sessions',
                        'action_required': f'Analyze {page_path} success',
                        'business_impact': 75,
                        'detected_at': datetime.now().isoformat()
                    })

                elif yesterday['sessions'] < min_val:
                    record_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': yesterday['date'],
                        'anomaly_type': 'record',
                        'priority': 'P1',
                        'record_type': 'low',
                        'dimension': 'landing_page',
                        'dimension_value': page_path,
                        'metric': 'sessions',
                        'value': yesterday['sessions'],
                        'previous_record': min_val,
                        'decline': round(((min_val - yesterday['sessions']) / min_val) * 100, 2),
                        'message': f'⚠️ {page_path} record low: {yesterday["sessions"]} sessions',
                        'action_required': f'Investigate {page_path} traffic loss',
                        'business_impact': 100,
                        'detected_at': datetime.now().isoformat()
                    })

    # Sort by priority (P1 first, then P3)
    record_alerts.sort(key=lambda x: (x['priority'], -x['business_impact']))

    print(f'  🏆 Found {len(record_alerts)} record alerts')
    return record_alerts


def main():
    """Process all properties and generate record alert report."""
    all_alerts = []
    data_dir = Path('data')

    # Process weekly_property_*.json files (90-day data)
    property_files = sorted(data_dir.glob('scout_production_clean_*.json'))

    if not property_files:
        print('❌ No property files found (looking for scout_production_clean_*.json)')
        print('   Run BigQuery export first to generate data files')
        return

    print(f'🔍 Processing {len(property_files)} properties for record detection...\n')

    for file_path in property_files:
        try:
            alerts = detect_record_alerts(str(file_path))
            all_alerts.extend(alerts)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'detector_type': 'record',
        'priority': 'P1-P3',
        'properties_analyzed': len(property_files),
        'total_alerts': len(all_alerts),
        'dimensions': ['overall', 'device', 'traffic_source', 'landing_page'],
        'alerts': all_alerts
    }

    # Save report
    output_file = data_dir / 'scout_record_alerts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n✅ Record detection complete')
    print(f'📊 Generated {len(all_alerts)} alerts')
    print(f'💾 Saved to: {output_file}')

    if all_alerts:
        print(f'\n🏆 RECORDS DETECTED:')
        highs = len([a for a in all_alerts if a['record_type'] == 'high'])
        lows = len([a for a in all_alerts if a['record_type'] == 'low'])
        print(f'  • New highs: {highs} (P3 - good news)')
        print(f'  • New lows: {lows} (P1 - investigate)')
    else:
        print(f'\n✅ No records broken (all metrics within historical range)')


if __name__ == '__main__':
    main()
