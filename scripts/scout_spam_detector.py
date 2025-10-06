#!/usr/bin/env python3
"""
SCOUT Spam Detector - P1 High Priority Alert System
[R18]: Spam detection with quality signal analysis
→ needs: clean-data, quality-signals
→ provides: spam-alerts

Algorithm: Z-score (threshold 3.0) + quality signals
BigQuery Window: DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY) to yesterday
Comparison: Yesterday vs 7-day average
Dimensions: Overall, Geography, Traffic Source
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple


def calculate_z_score(values: List[float]) -> List[Tuple[int, float, bool]]:
    """
    Calculate z-scores for a list of values.

    Args:
        values: List of metric values

    Returns:
        List of tuples (index, z_score, is_anomaly)
    """
    if len(values) < 3:
        return [(i, 0.0, False) for i in range(len(values))]

    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values) if len(values) > 1 else 0

    if stdev_val == 0:
        return [(i, 0.0, False) for i in range(len(values))]

    z_scores = []
    for i, value in enumerate(values):
        z_score = (value - mean_val) / stdev_val
        is_anomaly = abs(z_score) > 3.0  # Spam threshold: 3.0
        z_scores.append((i, z_score, is_anomaly))

    return z_scores


def has_spam_quality_signals(bounce_rate: float, avg_duration: float) -> bool:
    """
    Check if quality signals indicate spam/bot traffic.

    Args:
        bounce_rate: Bounce rate percentage (0-100)
        avg_duration: Average session duration in seconds

    Returns:
        True if spam indicators present
    """
    return bounce_rate > 85 or avg_duration < 10


def detect_spam_alerts(property_file: str) -> List[Dict]:
    """
    Detect spam/bot traffic using z-score + quality signal analysis.

    Args:
        property_file: Path to weekly_property_*.json file with 10-day data

    Returns:
        List of spam alerts for Overall, Geography, Traffic Source dimensions
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
    spam_alerts = []

    # Process OVERALL dimension
    # daily_overall = data.get('daily_overall', [])

    if len(daily_overall) >= 2:
        # Yesterday is most recent, calculate 7-day baseline (exclude yesterday)
        yesterday = daily_overall[-1]
        baseline_days = daily_overall[-8:-1] if len(daily_overall) >= 8 else daily_overall[:-1]

        sessions = [int(d.get('sessions', 0)) for d in baseline_days]
        yesterday_sessions = int(yesterday.get('sessions', 0))

        # Calculate z-score
        all_sessions = sessions + [yesterday_sessions]
        z_results = calculate_z_score(all_sessions)
        yesterday_z = z_results[-1]

        # Check quality signals
        bounce_rate = float(yesterday.get('bounce_rate', 0))
        avg_duration = float(yesterday.get('avg_session_duration', 0))
        has_spam_signals = has_spam_quality_signals(bounce_rate, avg_duration)

        if yesterday_z[2] and has_spam_signals:  # Z-score anomaly + quality signals
            spam_alerts.append({
                'property_id': property_id,
                'domain': domain,
                'date': yesterday['date'],
                'anomaly_type': 'spam',
                'priority': 'P1',
                'dimension': 'overall',
                'dimension_value': 'site-wide',
                'metric': 'sessions',
                'value': yesterday_sessions,
                'baseline': round(statistics.mean(sessions), 2),
                'z_score': round(abs(yesterday_z[1]), 2),
                'bounce_rate': round(bounce_rate, 2),
                'avg_session_duration': round(avg_duration, 2),
                'message': f'Spam traffic detected: {yesterday_sessions} sessions with {round(bounce_rate, 1)}% bounce rate',
                'action_required': 'Review traffic sources for bot activity',
                'business_impact': min(100, round(abs(yesterday_z[1]) * 25)),
                'detected_at': datetime.now().isoformat()
            })

    # Process GEOGRAPHY dimension
    geo_segments = file_data.get('geo_segments', [])
    if geo_segments:
        # Group by country
        country_data = {}
        for seg in geo_segments:
            country = seg.get('country', '')
            if not country or country == '':
                continue
            if country not in country_data:
                country_data[country] = []
            country_data[country].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0)),
                'bounce_rate': float(seg.get('bounce_rate', 0)),
                'avg_duration': float(seg.get('avg_session_duration', 0))
            })

        for country, points in country_data.items():
            if len(points) < 2:
                continue

            yesterday = points[-1]
            baseline = points[-8:-1] if len(points) >= 8 else points[:-1]

            sessions = [p['sessions'] for p in baseline]
            all_sessions = sessions + [yesterday['sessions']]
            z_results = calculate_z_score(all_sessions)
            yesterday_z = z_results[-1]

            has_spam_signals = has_spam_quality_signals(
                yesterday['bounce_rate'],
                yesterday['avg_duration']
            )

            if yesterday_z[2] and has_spam_signals:
                spam_alerts.append({
                    'property_id': property_id,
                    'domain': domain,
                    'date': yesterday['date'],
                    'anomaly_type': 'spam',
                    'priority': 'P1',
                    'dimension': 'geography',
                    'dimension_value': country,
                    'metric': 'sessions',
                    'value': yesterday['sessions'],
                    'baseline': round(statistics.mean(sessions), 2),
                    'z_score': round(abs(yesterday_z[1]), 2),
                    'bounce_rate': round(yesterday['bounce_rate'], 2),
                    'avg_session_duration': round(yesterday['avg_duration'], 2),
                    'message': f'Spam from {country}: {yesterday["sessions"]} sessions, {round(yesterday["bounce_rate"], 1)}% bounce',
                    'action_required': f'Review {country} traffic sources',
                    'business_impact': min(100, round(abs(yesterday_z[1]) * 25)),
                    'detected_at': datetime.now().isoformat()
                })

    # Process TRAFFIC SOURCE dimension
    traffic_segments = file_data.get('traffic_segments', [])
    if traffic_segments:
        # Group by source/medium
        source_data = {}
        for seg in traffic_segments:
            source_medium = f"{seg.get('source', '')}/{seg.get('medium', '')}"
            if source_medium not in source_data:
                source_data[source_medium] = []
            source_data[source_medium].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0)),
                'bounce_rate': float(seg.get('bounce_rate', 0)),
                'avg_duration': float(seg.get('avg_session_duration', 0))
            })

        for source_medium, points in source_data.items():
            if len(points) < 2:
                continue

            yesterday = points[-1]
            baseline = points[-8:-1] if len(points) >= 8 else points[:-1]

            sessions = [p['sessions'] for p in baseline]
            all_sessions = sessions + [yesterday['sessions']]
            z_results = calculate_z_score(all_sessions)
            yesterday_z = z_results[-1]

            has_spam_signals = has_spam_quality_signals(
                yesterday['bounce_rate'],
                yesterday['avg_duration']
            )

            if yesterday_z[2] and has_spam_signals:
                spam_alerts.append({
                    'property_id': property_id,
                    'domain': domain,
                    'date': yesterday['date'],
                    'anomaly_type': 'spam',
                    'priority': 'P1',
                    'dimension': 'traffic_source',
                    'dimension_value': source_medium,
                    'metric': 'sessions',
                    'value': yesterday['sessions'],
                    'baseline': round(statistics.mean(sessions), 2),
                    'z_score': round(abs(yesterday_z[1]), 2),
                    'bounce_rate': round(yesterday['bounce_rate'], 2),
                    'avg_session_duration': round(yesterday['avg_duration'], 2),
                    'message': f'Spam from {source_medium}: {yesterday["sessions"]} sessions, {round(yesterday["bounce_rate"], 1)}% bounce',
                    'action_required': f'Block or filter {source_medium} if spam confirmed',
                    'business_impact': min(100, round(abs(yesterday_z[1]) * 25)),
                    'detected_at': datetime.now().isoformat()
                })

    print(f'  🟠 Found {len(spam_alerts)} spam alerts')
    return spam_alerts


def main():
    """Process all properties and generate spam alert report."""
    all_alerts = []
    data_dir = Path('data')

    # Process weekly_property_*.json files (10-day data)
    property_files = sorted(data_dir.glob('scout_production_clean_*.json'))

    if not property_files:
        print('❌ No property files found (looking for scout_production_clean_*.json)')
        print('   Run BigQuery export first to generate data files')
        return

    print(f'🔍 Processing {len(property_files)} properties for spam detection...\n')

    for file_path in property_files:
        try:
            alerts = detect_spam_alerts(str(file_path))
            all_alerts.extend(alerts)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'detector_type': 'spam',
        'priority': 'P1',
        'properties_analyzed': len(property_files),
        'total_alerts': len(all_alerts),
        'dimensions': ['overall', 'geography', 'traffic_source'],
        'alerts': all_alerts
    }

    # Save report
    output_file = data_dir / 'scout_spam_alerts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n✅ Spam detection complete')
    print(f'📊 Generated {len(all_alerts)} P1 alerts')
    print(f'💾 Saved to: {output_file}')

    if all_alerts:
        print(f'\n🟠 SPAM TRAFFIC DETECTED:')
        dimension_counts = {}
        for alert in all_alerts:
            dim = alert['dimension']
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1

        for dim, count in dimension_counts.items():
            print(f'  • {dim}: {count} alerts')
    else:
        print(f'\n✅ No spam detected (all traffic appears legitimate)')


if __name__ == '__main__':
    main()
