#!/usr/bin/env python3
"""
SCOUT Segment-Level Anomaly Detection Engine
Detects anomalies within device, geography, and traffic source segments

[R14]: Segment-level anomaly detection
→ needs: segmented raw data files
→ provides: device/geo/traffic/landing_page anomalies
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def calculate_z_score_anomalies(values: List[float], threshold: float = 2.0):
    """Calculate z-score anomalies for a metric series"""
    if len(values) < 3:
        return [(i, 0.0, False) for i in range(len(values))]

    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values) if len(values) > 1 else 0

    if stdev_val == 0:
        return [(i, 0.0, False) for i in range(len(values))]

    z_scores = []
    for i, value in enumerate(values):
        z_score = (value - mean_val) / stdev_val
        is_anomaly = abs(z_score) > threshold
        z_scores.append((i, z_score, is_anomaly))

    return z_scores


def detect_segment_anomalies(property_file: str) -> List[Dict]:
    """Detect anomalies within segments for a single property"""
    print(f'📊 Processing: {Path(property_file).name}')

    # Read UTF-16 encoded file
    with open(property_file, 'r', encoding='utf-16') as f:
        raw_data = f.read()

    # Strip BOM if present
    raw_data = raw_data.lstrip('\ufeff')
    data = json.loads(raw_data)[0]

    property_id = data['property_id']
    domain = data['domain']
    all_anomalies = []

    # Process DEVICE segments
    device_segments = data.get('device_segments', [])
    if device_segments:
        device_data = {}
        for seg in device_segments:
            device = seg['device_category']
            if device not in device_data:
                device_data[device] = []
            device_data[device].append({
                'date': seg['date'],
                'sessions': int(seg['sessions']),
                'users': int(seg['users']),
                'page_views': int(seg['page_views'])
            })

        for device, points in device_data.items():
            if len(points) < 3:
                continue

            sessions = [p['sessions'] for p in points]
            z_results = calculate_z_score_anomalies(sessions)

            for i, (idx, z_score, is_anomaly) in enumerate(z_results):
                if is_anomaly and abs(z_score) > 2.0:
                    direction = 'spike' if points[i]['sessions'] > statistics.mean(sessions) else 'drop'
                    all_anomalies.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': points[i]['date'],
                        'segment_type': 'device',
                        'segment_value': device,
                        'metric': 'sessions',
                        'value': points[i]['sessions'],
                        'mean': round(statistics.mean(sessions), 2),
                        'z_score': round(abs(z_score), 2),
                        'direction': direction,
                        'detection_methods': 'z-score',
                        'business_impact': min(100, round(abs(z_score) * 30)),
                        'priority': 'warning' if abs(z_score) > 2.5 else 'normal'
                    })

    # Process GEO segments
    geo_segments = data.get('geo_segments', [])
    if geo_segments:
        country_data = {}
        for seg in geo_segments:
            country = seg['country']
            if not country or country == '':
                continue
            if country not in country_data:
                country_data[country] = []
            country_data[country].append({
                'date': seg['date'],
                'sessions': int(seg['sessions']),
                'users': int(seg['users'])
            })

        for country, points in country_data.items():
            if len(points) < 3:
                continue

            sessions = [p['sessions'] for p in points]
            z_results = calculate_z_score_anomalies(sessions)

            for i, (idx, z_score, is_anomaly) in enumerate(z_results):
                if is_anomaly and abs(z_score) > 2.0:
                    direction = 'spike' if points[i]['sessions'] > statistics.mean(sessions) else 'drop'
                    all_anomalies.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': points[i]['date'],
                        'segment_type': 'geography',
                        'segment_value': country,
                        'metric': 'sessions',
                        'value': points[i]['sessions'],
                        'mean': round(statistics.mean(sessions), 2),
                        'z_score': round(abs(z_score), 2),
                        'direction': direction,
                        'detection_methods': 'z-score',
                        'business_impact': min(100, round(abs(z_score) * 30)),
                        'priority': 'warning' if abs(z_score) > 2.5 else 'normal'
                    })

    # Process TRAFFIC SOURCE segments
    traffic_segments = data.get('traffic_segments', [])
    if traffic_segments:
        source_data = {}
        for seg in traffic_segments:
            source = f"{seg['source']}/{seg['medium']}"
            if source not in source_data:
                source_data[source] = []
            source_data[source].append({
                'date': seg['date'],
                'sessions': int(seg['sessions']),
                'users': int(seg['users'])
            })

        for source, points in source_data.items():
            if len(points) < 3:
                continue

            sessions = [p['sessions'] for p in points]
            z_results = calculate_z_score_anomalies(sessions)

            for i, (idx, z_score, is_anomaly) in enumerate(z_results):
                if is_anomaly and abs(z_score) > 2.0:
                    direction = 'spike' if points[i]['sessions'] > statistics.mean(sessions) else 'drop'
                    all_anomalies.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': points[i]['date'],
                        'segment_type': 'traffic_source',
                        'segment_value': source,
                        'metric': 'sessions',
                        'value': points[i]['sessions'],
                        'mean': round(statistics.mean(sessions), 2),
                        'z_score': round(abs(z_score), 2),
                        'direction': direction,
                        'detection_methods': 'z-score',
                        'business_impact': min(100, round(abs(z_score) * 30)),
                        'priority': 'warning' if abs(z_score) > 2.5 else 'normal'
                    })

    # Process LANDING PAGE segments
    landing_segments = data.get('landing_page_segments', [])
    if landing_segments:
        page_data = {}
        for seg in landing_segments:
            page = seg['landing_page']
            if not page or page == '':
                continue
            if page not in page_data:
                page_data[page] = []
            page_data[page].append({
                'date': seg['date'],
                'sessions': int(seg['sessions']),
                'users': int(seg['users']),
                'page_views': int(seg['page_views'])
            })

        for page, points in page_data.items():
            if len(points) < 3:
                continue

            sessions = [p['sessions'] for p in points]
            z_results = calculate_z_score_anomalies(sessions)

            for i, (idx, z_score, is_anomaly) in enumerate(z_results):
                if is_anomaly and abs(z_score) > 2.0:
                    direction = 'spike' if points[i]['sessions'] > statistics.mean(sessions) else 'drop'
                    all_anomalies.append({
                        'property_id': property_id,
                        'domain': domain,
                        'date': points[i]['date'],
                        'segment_type': 'landing_page',
                        'segment_value': page,
                        'metric': 'sessions',
                        'value': points[i]['sessions'],
                        'mean': round(statistics.mean(sessions), 2),
                        'z_score': round(abs(z_score), 2),
                        'direction': direction,
                        'detection_methods': 'z-score',
                        'business_impact': min(100, round(abs(z_score) * 30)),
                        'priority': 'warning' if abs(z_score) > 2.5 else 'normal'
                    })

    print(f'  ✅ Found {len(all_anomalies)} segment-level anomalies')
    return all_anomalies


def main():
    """Main execution for segment-level anomaly detection"""
    print("🚀 SCOUT Segment-Level Anomaly Detection Engine")
    print("=" * 60)

    # Process all segmented property files
    all_anomalies = []
    data_dir = Path('data')
    segmented_files = list(data_dir.glob('segmented_property_*.json'))

    print(f'\n📂 Processing {len(segmented_files)} segmented property files...\n')

    for file_path in segmented_files:
        try:
            anomalies = detect_segment_anomalies(str(file_path))
            all_anomalies.extend(anomalies)
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

    # Sort by business impact
    all_anomalies.sort(key=lambda x: x['business_impact'], reverse=True)

    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'properties_analyzed': len(segmented_files),
        'total_anomalies': len(all_anomalies),
        'segment_types': ['device', 'geography', 'traffic_source', 'landing_page'],
        'anomalies': all_anomalies
    }

    # Save report
    output_file = 'data/scout_segment_level_anomalies.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f'\n' + '=' * 60)
    print(f'✅ Generated {len(all_anomalies)} segment-level anomalies')
    print(f'📊 Saved to: {output_file}')
    print(f'\n📈 Segment breakdown:')
    print(f'  Device: {len([a for a in all_anomalies if a["segment_type"] == "device"])}')
    print(f'  Geography: {len([a for a in all_anomalies if a["segment_type"] == "geography"])}')
    print(f'  Traffic Source: {len([a for a in all_anomalies if a["segment_type"] == "traffic_source"])}')
    print(f'  Landing Page: {len([a for a in all_anomalies if a["segment_type"] == "landing_page"])}')
    print(f'\n🎯 Top 5 anomalies by business impact:')
    for i, anomaly in enumerate(all_anomalies[:5], 1):
        print(f"  {i}. [{anomaly['segment_type']}] {anomaly['segment_value']} - "
              f"{anomaly['date']} - Impact: {anomaly['business_impact']}")


if __name__ == "__main__":
    main()
