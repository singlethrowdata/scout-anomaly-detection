#!/usr/bin/env python3
"""
SCOUT Trend Detector - P2-P3 Lower Priority Alert System
[R20]: Trend detection for directional changes
→ needs: historical-data-180day
→ provides: trend-alerts

Algorithm: Moving average crossover
BigQuery Window: DATE_SUB(CURRENT_DATE(), INTERVAL 183 DAY) to yesterday
Comparison: Last 30 days avg vs previous 180 days avg
Dimensions: Overall, Geography, Landing Pages, Devices, Traffic Source
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def detect_trend_alerts(property_file: str, min_sessions: int = 50, threshold_pct: float = 15.0) -> List[Dict]:
    """
    Detect 30-day vs 180-day trend changes.

    Args:
        property_file: Path to weekly_property_*.json file with 180-day data
        min_sessions: Minimum daily sessions to qualify (default: 50)
        threshold_pct: Minimum percentage change to trigger alert (default: 15%)

    Returns:
        List of trend alerts for qualified segments
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
    trend_alerts = []

    # Process OVERALL dimension
    # daily_overall = data.get('daily_overall', [])

    if len(daily_overall) >= 31:  # Need at least 31 days for 30-day average
        # Last 30 days (excluding today)
        recent_30 = daily_overall[-31:-1]
        # Previous 150 days (180 total - 30 recent)
        baseline_150 = daily_overall[:-31] if len(daily_overall) > 31 else []

        if baseline_150:
            recent_sessions = [int(d.get('sessions', 0)) for d in recent_30]
            baseline_sessions = [int(d.get('sessions', 0)) for d in baseline_150]

            recent_avg = statistics.mean(recent_sessions)
            baseline_avg = statistics.mean(baseline_sessions)

            # Only process if meets minimum volume
            if recent_avg >= min_sessions and baseline_avg > 0:
                change_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100

                if abs(change_pct) >= threshold_pct:
                    trend_direction = 'up' if change_pct > 0 else 'down'
                    priority = 'P2' if trend_direction == 'down' else 'P3'

                    trend_alerts.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': daily_overall[-1]['date'],
                        'anomaly_type': 'trend',
                        'priority': priority,
                        'trend_direction': trend_direction,
                        'dimension': 'overall',
                        'dimension_value': 'site-wide',
                        'metric': 'sessions',
                        'recent_30_day_avg': round(recent_avg, 2),
                        'baseline_180_day_avg': round(baseline_avg, 2),
                        'change_percentage': round(change_pct, 2),
                        'message': f'{"↗️" if trend_direction == "up" else "↘️"} {abs(round(change_pct, 1))}% trend {trend_direction}: 30-day avg is {round(recent_avg, 0)} vs baseline {round(baseline_avg, 0)}',
                        'action_required': f'{"Capitalize on growth" if trend_direction == "up" else "Address declining traffic"}',
                        'business_impact': min(100, round(abs(change_pct) * 3)),
                        'detected_at': datetime.now().isoformat()
                    })

    # Process GEOGRAPHY dimension
    geo_segments = file_data.get('geo_segments', [])
    if geo_segments:
        country_data = {}
        for seg in geo_segments:
            country = seg.get('country', '')
            if not country or country == '':
                continue
            if country not in country_data:
                country_data[country] = []
            country_data[country].append({
                'date': seg['date'],
                'sessions': int(seg.get('sessions', 0))
            })

        for country, points in country_data.items():
            if len(points) >= 31:
                recent_30 = points[-31:-1]
                baseline_150 = points[:-31]

                if baseline_150:
                    recent_sessions = [p['sessions'] for p in recent_30]
                    baseline_sessions = [p['sessions'] for p in baseline_150]

                    recent_avg = statistics.mean(recent_sessions)
                    baseline_avg = statistics.mean(baseline_sessions)

                    if recent_avg >= min_sessions and baseline_avg > 0:
                        change_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100

                        if abs(change_pct) >= threshold_pct:
                            trend_direction = 'up' if change_pct > 0 else 'down'
                            priority = 'P2' if trend_direction == 'down' else 'P3'

                            trend_alerts.append({
                                'property_id': property_id,
                                'domain': domain,
                                'date': points[-1]['date'],
                                'anomaly_type': 'trend',
                                'priority': priority,
                                'trend_direction': trend_direction,
                                'dimension': 'geography',
                                'dimension_value': country,
                                'metric': 'sessions',
                                'recent_30_day_avg': round(recent_avg, 2),
                                'baseline_180_day_avg': round(baseline_avg, 2),
                                'change_percentage': round(change_pct, 2),
                                'message': f'{country}: {"↗️" if trend_direction == "up" else "↘️"} {abs(round(change_pct, 1))}% trend',
                                'action_required': f'{"Expand {country} presence" if trend_direction == "up" else "Investigate {country} decline"}',
                                'business_impact': min(100, round(abs(change_pct) * 3)),
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
            if len(points) >= 31:
                recent_30 = points[-31:-1]
                baseline_150 = points[:-31]

                if baseline_150:
                    recent_sessions = [p['sessions'] for p in recent_30]
                    baseline_sessions = [p['sessions'] for p in baseline_150]

                    recent_avg = statistics.mean(recent_sessions)
                    baseline_avg = statistics.mean(baseline_sessions)

                    if recent_avg >= min_sessions and baseline_avg > 0:
                        change_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100

                        if abs(change_pct) >= threshold_pct:
                            trend_direction = 'up' if change_pct > 0 else 'down'
                            priority = 'P2' if trend_direction == 'down' else 'P3'

                            trend_alerts.append({
                                'property_id': property_id,
                                'domain': domain,
                                'date': points[-1]['date'],
                                'anomaly_type': 'trend',
                                'priority': priority,
                                'trend_direction': trend_direction,
                                'dimension': 'device',
                                'dimension_value': device,
                                'metric': 'sessions',
                                'recent_30_day_avg': round(recent_avg, 2),
                                'baseline_180_day_avg': round(baseline_avg, 2),
                                'change_percentage': round(change_pct, 2),
                                'message': f'{device}: {"↗️" if trend_direction == "up" else "↘️"} {abs(round(change_pct, 1))}% trend',
                                'action_required': f'{"Optimize {device} experience" if trend_direction == "up" else "Fix {device} issues"}',
                                'business_impact': min(100, round(abs(change_pct) * 3)),
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
            if len(points) >= 31:
                recent_30 = points[-31:-1]
                baseline_150 = points[:-31]

                if baseline_150:
                    recent_sessions = [p['sessions'] for p in recent_30]
                    baseline_sessions = [p['sessions'] for p in baseline_150]

                    recent_avg = statistics.mean(recent_sessions)
                    baseline_avg = statistics.mean(baseline_sessions)

                    if recent_avg >= min_sessions and baseline_avg > 0:
                        change_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100

                        if abs(change_pct) >= threshold_pct:
                            trend_direction = 'up' if change_pct > 0 else 'down'
                            priority = 'P2' if trend_direction == 'down' else 'P3'

                            trend_alerts.append({
                                'property_id': property_id,
                                'domain': domain,
                                'date': points[-1]['date'],
                                'anomaly_type': 'trend',
                                'priority': priority,
                                'trend_direction': trend_direction,
                                'dimension': 'traffic_source',
                                'dimension_value': source_medium,
                                'metric': 'sessions',
                                'recent_30_day_avg': round(recent_avg, 2),
                                'baseline_180_day_avg': round(baseline_avg, 2),
                                'change_percentage': round(change_pct, 2),
                                'message': f'{source_medium}: {"↗️" if trend_direction == "up" else "↘️"} {abs(round(change_pct, 1))}% trend',
                                'action_required': f'{"Scale {source_medium} investment" if trend_direction == "up" else "Review {source_medium} strategy"}',
                                'business_impact': min(100, round(abs(change_pct) * 3)),
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
            if len(points) >= 31:
                recent_30 = points[-31:-1]
                baseline_150 = points[:-31]

                if baseline_150:
                    recent_sessions = [p['sessions'] for p in recent_30]
                    baseline_sessions = [p['sessions'] for p in baseline_150]

                    recent_avg = statistics.mean(recent_sessions)
                    baseline_avg = statistics.mean(baseline_sessions)

                    if recent_avg >= min_sessions and baseline_avg > 0:
                        change_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100

                        if abs(change_pct) >= threshold_pct:
                            trend_direction = 'up' if change_pct > 0 else 'down'
                            priority = 'P2' if trend_direction == 'down' else 'P3'

                            trend_alerts.append({
                                'property_id': property_id,
                                'domain': domain,
                                'date': points[-1]['date'],
                                'anomaly_type': 'trend',
                                'priority': priority,
                                'trend_direction': trend_direction,
                                'dimension': 'landing_page',
                                'dimension_value': page_path,
                                'metric': 'sessions',
                                'recent_30_day_avg': round(recent_avg, 2),
                                'baseline_180_day_avg': round(baseline_avg, 2),
                                'change_percentage': round(change_pct, 2),
                                'message': f'{page_path}: {"↗️" if trend_direction == "up" else "↘️"} {abs(round(change_pct, 1))}% trend',
                                'action_required': f'{"Promote {page_path} content" if trend_direction == "up" else "Review {page_path} performance"}',
                                'business_impact': min(100, round(abs(change_pct) * 3)),
                                'detected_at': datetime.now().isoformat()
                            })

    # Sort by priority (P2 negative trends first, then P3 positive)
    trend_alerts.sort(key=lambda x: (x['priority'], -x['business_impact']))

    print(f'  📈 Found {len(trend_alerts)} trend alerts')
    return trend_alerts


def main():
    """Process all properties and generate trend alert report."""
    all_alerts = []
    data_dir = Path('data')

    # Process weekly_property_*.json files (180-day data)
    property_files = sorted(data_dir.glob('scout_production_clean_*.json'))

    if not property_files:
        print('❌ No property files found (looking for scout_production_clean_*.json)')
        print('   Run BigQuery export first to generate data files')
        return

    print(f'🔍 Processing {len(property_files)} properties for trend detection...\n')

    for file_path in property_files:
        try:
            alerts = detect_trend_alerts(str(file_path))
            all_alerts.extend(alerts)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'detector_type': 'trend',
        'priority': 'P2-P3',
        'properties_analyzed': len(property_files),
        'total_alerts': len(all_alerts),
        'dimensions': ['overall', 'geography', 'device', 'traffic_source', 'landing_page'],
        'alerts': all_alerts
    }

    # Save report
    output_file = data_dir / 'scout_trend_alerts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n✅ Trend detection complete')
    print(f'📊 Generated {len(all_alerts)} alerts')
    print(f'💾 Saved to: {output_file}')

    if all_alerts:
        print(f'\n📈 TRENDS DETECTED:')
        uptrends = len([a for a in all_alerts if a['trend_direction'] == 'up'])
        downtrends = len([a for a in all_alerts if a['trend_direction'] == 'down'])
        print(f'  • Upward trends: {uptrends} (P3 - good news)')
        print(f'  • Downward trends: {downtrends} (P2 - investigate)')
    else:
        print(f'\n✅ No significant trends detected (all metrics stable)')


if __name__ == '__main__':
    main()
