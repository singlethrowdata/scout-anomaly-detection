#!/usr/bin/env python3
"""
SCOUT Anomaly Detection Engine
Multi-method statistical anomaly detection for real GA4 data

[R5]: Multi-method statistical anomaly detection
→ needs: clean-data
→ provides: raw-anomalies

[R6]: Business impact scoring for prioritization
→ needs: raw-anomalies, conversion-tracking
→ provides: prioritized-alerts
"""

import json
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple

def load_clean_data(file_path: str) -> Dict[str, Any]:
    """Load clean dataset from SCOUT data processor"""

    print(f"📊 Loading Clean Dataset: {file_path}")
    print("-" * 50)

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        clean_dataset = data['clean_dataset']
        client_name = data['client_metadata']['client_name']

        print(f"✅ Client: {client_name}")
        print(f"✅ Records: {len(clean_dataset)} days")
        print(f"✅ Date range: {clean_dataset[-1]['date']} to {clean_dataset[0]['date']}")

        return data

    except Exception as e:
        print(f"❌ Failed to load clean data: {e}")
        return {}

def calculate_z_score_anomalies(values: List[float], threshold: float = 2.0) -> List[Tuple[int, float, bool]]:
    """Calculate z-score anomalies for a metric series"""

    if len(values) < 3:  # Need minimum data for meaningful statistics
        return [(i, 0.0, False) for i in range(len(values))]

    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values) if len(values) > 1 else 0

    if stdev_val == 0:  # No variation in data
        return [(i, 0.0, False) for i in range(len(values))]

    z_scores = []
    for i, value in enumerate(values):
        z_score = (value - mean_val) / stdev_val
        is_anomaly = abs(z_score) > threshold
        z_scores.append((i, z_score, is_anomaly))

    return z_scores

def calculate_iqr_anomalies(values: List[float], multiplier: float = 1.5) -> List[Tuple[int, float, bool]]:
    """Calculate IQR-based anomalies for a metric series"""

    if len(values) < 4:  # Need minimum data for quartiles
        return [(i, 0.0, False) for i in range(len(values))]

    sorted_values = sorted(values)
    n = len(sorted_values)

    # Calculate quartiles
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_values[q1_idx]
    q3 = sorted_values[q3_idx]

    iqr = q3 - q1
    if iqr == 0:  # No variation
        return [(i, 0.0, False) for i in range(len(values))]

    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    results = []
    for i, value in enumerate(values):
        distance_from_bounds = 0.0
        is_anomaly = False

        if value < lower_bound:
            distance_from_bounds = (lower_bound - value) / iqr
            is_anomaly = True
        elif value > upper_bound:
            distance_from_bounds = (value - upper_bound) / iqr
            is_anomaly = True

        results.append((i, distance_from_bounds, is_anomaly))

    return results

def detect_anomalies_for_metric(data: List[Dict], metric: str) -> Dict[str, Any]:
    """Detect anomalies for a specific metric using multiple methods"""

    # Extract metric values in chronological order (reverse since data is newest first)
    values = [day[metric] for day in reversed(data)]
    dates = [day['date'] for day in reversed(data)]

    print(f"  📈 Analyzing {metric}: {values}")

    # Apply both detection methods
    z_score_results = calculate_z_score_anomalies(values)
    iqr_results = calculate_iqr_anomalies(values)

    # Combine results
    anomalies = []
    for i in range(len(values)):
        date = dates[i]
        value = values[i]

        z_idx, z_score, z_anomaly = z_score_results[i]
        iqr_idx, iqr_distance, iqr_anomaly = iqr_results[i]

        # Consensus approach: anomaly if detected by either method
        is_anomaly = z_anomaly or iqr_anomaly

        # Calculate severity (higher = more severe)
        severity = max(abs(z_score), iqr_distance)

        # Determine anomaly type
        anomaly_type = "normal"
        if is_anomaly:
            if value < statistics.mean(values):
                anomaly_type = "below_normal"
            else:
                anomaly_type = "above_normal"

        anomaly_record = {
            'date': date,
            'metric': metric,
            'value': value,
            'is_anomaly': is_anomaly,
            'anomaly_type': anomaly_type,
            'severity': round(severity, 3),
            'detection_methods': {
                'z_score': {'score': round(z_score, 3), 'anomaly': z_anomaly},
                'iqr': {'distance': round(iqr_distance, 3), 'anomaly': iqr_anomaly}
            }
        }

        anomalies.append(anomaly_record)

    # Filter to only anomalies for summary
    detected_anomalies = [a for a in anomalies if a['is_anomaly']]

    print(f"    🚨 Anomalies detected: {len(detected_anomalies)}")
    for anomaly in detected_anomalies:
        print(f"      - {anomaly['date']}: {anomaly['value']} ({anomaly['anomaly_type']}, severity: {anomaly['severity']})")

    return {
        'metric': metric,
        'total_points': len(values),
        'anomalies_detected': len(detected_anomalies),
        'anomaly_rate': len(detected_anomalies) / len(values) if values else 0,
        'all_points': anomalies,
        'anomalies_only': detected_anomalies,
        'statistics': {
            'mean': round(statistics.mean(values), 2) if values else 0,
            'median': round(statistics.median(values), 2) if values else 0,
            'stdev': round(statistics.stdev(values), 2) if len(values) > 1 else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0
        }
    }

def calculate_business_impact_score(anomaly: Dict[str, Any], baseline_stats: Dict[str, Any]) -> float:
    """Calculate business impact score for an anomaly (0-100)"""

    metric = anomaly['metric']
    value = anomaly['value']
    severity = anomaly['severity']
    anomaly_type = anomaly['anomaly_type']

    # Base impact from severity
    impact_score = min(severity * 20, 80)  # Cap at 80, leave room for business multipliers

    # Business criticality multipliers
    business_multipliers = {
        'sessions': 1.0,      # High impact - core traffic
        'users': 1.2,        # Higher impact - unique visitors matter more
        'conversions': 2.0,   # Critical impact - directly affects revenue
        'page_views': 0.8     # Lower impact - engagement metric
    }

    multiplier = business_multipliers.get(metric, 1.0)
    impact_score *= multiplier

    # Direction matters for business impact
    if metric in ['sessions', 'users', 'conversions', 'page_views']:
        if anomaly_type == 'below_normal':
            # Drops are worse for business metrics
            impact_score *= 1.3
        # Spikes might be good, but still anomalies worth investigating

    # Scale relative to baseline
    if baseline_stats.get('mean', 0) > 0:
        relative_change = abs(value - baseline_stats['mean']) / baseline_stats['mean']
        if relative_change > 0.5:  # >50% change
            impact_score *= 1.4
        elif relative_change > 0.25:  # >25% change
            impact_score *= 1.2

    return min(round(impact_score, 1), 100.0)  # Cap at 100

def run_anomaly_detection(clean_data_file: str) -> Dict[str, Any]:
    """Run complete anomaly detection pipeline"""

    print("🚀 SCOUT Anomaly Detection Engine")
    print("=" * 60)

    # Load clean data
    data_package = load_clean_data(clean_data_file)
    if not data_package:
        return {'success': False, 'error': 'Failed to load clean data'}

    clean_dataset = data_package['clean_dataset']
    client_metadata = data_package['client_metadata']

    print(f"\n🔍 Multi-Method Anomaly Detection")
    print("-" * 40)
    print(f"Client: {client_metadata['client_name']}")
    print(f"Property: {client_metadata['property_id']}")

    # Metrics to analyze
    metrics_to_analyze = ['sessions', 'users', 'page_views', 'conversions']

    detection_results = {}
    all_anomalies = []

    # Run detection for each metric
    for metric in metrics_to_analyze:
        print(f"\n🎯 Detecting anomalies in {metric}")
        result = detect_anomalies_for_metric(clean_dataset, metric)
        detection_results[metric] = result

        # Calculate business impact for each anomaly
        for anomaly in result['anomalies_only']:
            impact_score = calculate_business_impact_score(anomaly, result['statistics'])
            anomaly['business_impact_score'] = impact_score

            # Add client context
            anomaly['client_name'] = client_metadata['client_name']
            anomaly['property_id'] = client_metadata['property_id']

            all_anomalies.append(anomaly)

    # Sort anomalies by business impact (highest first)
    all_anomalies.sort(key=lambda x: x['business_impact_score'], reverse=True)

    # Summary statistics
    total_anomalies = len(all_anomalies)
    high_impact_anomalies = [a for a in all_anomalies if a['business_impact_score'] >= 70]
    medium_impact_anomalies = [a for a in all_anomalies if 40 <= a['business_impact_score'] < 70]
    low_impact_anomalies = [a for a in all_anomalies if a['business_impact_score'] < 40]

    # Create final results
    results = {
        'processing_metadata': {
            'timestamp': datetime.now().isoformat(),
            'client_name': client_metadata['client_name'],
            'property_id': client_metadata['property_id'],
            'data_source': clean_data_file,
            'detection_methods': ['z_score', 'iqr'],
            'metrics_analyzed': metrics_to_analyze
        },
        'summary': {
            'total_anomalies': total_anomalies,
            'high_impact': len(high_impact_anomalies),
            'medium_impact': len(medium_impact_anomalies),
            'low_impact': len(low_impact_anomalies),
            'anomaly_rate': round(total_anomalies / (len(clean_dataset) * len(metrics_to_analyze)), 3)
        },
        'anomalies_by_impact': {
            'high_impact': high_impact_anomalies,
            'medium_impact': medium_impact_anomalies,
            'low_impact': low_impact_anomalies
        },
        'detection_results': detection_results,
        'all_anomalies': all_anomalies
    }

    return {'success': True, 'results': results}

def main():
    """Main execution for SCOUT anomaly detection"""

    # Process the real singlethrow.com data
    clean_data_file = "data/scout_production_clean_249571600.json"

    detection_result = run_anomaly_detection(clean_data_file)

    if not detection_result.get('success'):
        print(f"❌ Anomaly detection failed: {detection_result.get('error')}")
        return

    results = detection_result['results']

    # Display results
    print("\n🎯 SCOUT Anomaly Detection Results")
    print("=" * 60)

    summary = results['summary']
    print(f"✅ Total anomalies detected: {summary['total_anomalies']}")
    print(f"🔴 High impact (≥70): {summary['high_impact']}")
    print(f"🟡 Medium impact (40-69): {summary['medium_impact']}")
    print(f"🟢 Low impact (<40): {summary['low_impact']}")
    print(f"📊 Overall anomaly rate: {summary['anomaly_rate']:.1%}")

    # Show top anomalies
    if results['all_anomalies']:
        print(f"\n🚨 Top Anomalies by Business Impact:")
        print("-" * 45)
        for i, anomaly in enumerate(results['all_anomalies'][:5], 1):
            print(f"{i}. {anomaly['date']} - {anomaly['metric']}")
            print(f"   Value: {anomaly['value']} ({anomaly['anomaly_type']})")
            print(f"   Impact Score: {anomaly['business_impact_score']}/100")
            print(f"   Severity: {anomaly['severity']}")
            print()

    # Export results
    output_file = f"data/scout_anomalies_{results['processing_metadata']['property_id']}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Anomaly detection results exported: {output_file}")

    print("\n🔄 Next Step: Build intelligent alerting system using these prioritized anomalies")
    print("📊 SCOUT anomaly detection engine operational with real client data!")

if __name__ == "__main__":
    main()
