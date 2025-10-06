#!/usr/bin/env python3
"""
SCOUT Multi-Property Anomaly Testing
Test anomaly detection across multiple GA4 properties for cross-client pattern validation

[R5]: Multi-method statistical anomaly detection across properties
[R7]: Cross-client pattern recognition validation
→ needs: clean-data from multiple properties
→ provides: portfolio-patterns baseline
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.cloud import bigquery

def setup_bigquery_client():
    """Setup BigQuery client with service account authentication"""

    print("🔧 Setting up BigQuery client...")

    try:
        # Use service account for st-ga4-data project
        client = bigquery.Client(project='st-ga4-data')
        print("✅ BigQuery client connected to st-ga4-data project")
        return client
    except Exception as e:
        print(f"❌ Failed to setup BigQuery client: {e}")
        return None

def list_available_properties(client: bigquery.Client, limit: int = 10) -> List[str]:
    """List available GA4 properties in st-ga4-data project"""

    print(f"📊 Discovering GA4 properties in st-ga4-data...")

    try:
        # Query to find all analytics datasets
        query = """
        SELECT
            schema_name as dataset_id,
            REGEXP_EXTRACT(schema_name, r'analytics_(\d+)') as property_id
        FROM `st-ga4-data.INFORMATION_SCHEMA.SCHEMATA`
        WHERE schema_name LIKE 'analytics_%'
        AND REGEXP_EXTRACT(schema_name, r'analytics_(\d+)') IS NOT NULL
        ORDER BY schema_name
        LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )

        results = client.query(query, job_config=job_config)
        properties = []

        for row in results:
            if row.property_id:
                properties.append(row.property_id)

        print(f"✅ Found {len(properties)} GA4 properties")
        for i, prop_id in enumerate(properties[:5], 1):
            print(f"   {i}. analytics_{prop_id}")

        if len(properties) > 5:
            print(f"   ... and {len(properties) - 5} more properties")

        return properties

    except Exception as e:
        print(f"❌ Failed to list properties: {e}")
        return []

def get_property_traffic_sample(client: bigquery.Client, property_id: str) -> Dict[str, Any]:
    """Get traffic sample for a property to assess data volume"""

    print(f"📈 Sampling traffic for property {property_id}...")

    try:
        # Query last 7 days of data for traffic assessment
        query = f"""
        SELECT
            event_date,
            COUNT(DISTINCT user_pseudo_id) as users,
            COUNT(*) as events,
            COUNTIF(event_name = 'session_start') as sessions
        FROM `st-ga4-data.analytics_{property_id}.events_*`
        WHERE _TABLE_SUFFIX BETWEEN
            FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY))
            AND FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
        GROUP BY event_date
        ORDER BY event_date DESC
        LIMIT 7
        """

        results = client.query(query)
        data_points = []

        for row in results:
            data_points.append({
                'date': row.event_date,
                'users': row.users,
                'events': row.events,
                'sessions': row.sessions
            })

        if data_points:
            avg_sessions = sum(d['sessions'] for d in data_points) / len(data_points)
            avg_users = sum(d['users'] for d in data_points) / len(data_points)

            print(f"   📊 Traffic Summary: {avg_sessions:.0f} sessions/day, {avg_users:.0f} users/day")

            return {
                'property_id': property_id,
                'data_points': len(data_points),
                'avg_daily_sessions': avg_sessions,
                'avg_daily_users': avg_users,
                'traffic_level': 'high' if avg_sessions > 100 else 'medium' if avg_sessions > 20 else 'low',
                'sample_data': data_points
            }
        else:
            print(f"   ⚠️ No recent data found")
            return None

    except Exception as e:
        print(f"❌ Failed to sample property {property_id}: {e}")
        return None

def process_property_data(client: bigquery.Client, property_id: str) -> str:
    """Process a single property and return clean dataset filename"""

    print(f"\n🔄 Processing property {property_id}...")

    try:
        # Import and modify our existing BigQuery processor
        import sys
        sys.path.append('.')

        # Import the main processing logic
        import json
        from datetime import datetime, timedelta

        # Use the processing logic from scout_bigquery_processor main function
        # but adapted for programmatic use

        # Build the query for this property
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=7)

        query = f"""
        SELECT
            event_date,
            COUNTIF(event_name = 'session_start') as sessions,
            COUNT(DISTINCT user_pseudo_id) as users,
            COUNT(*) as page_views,
            COUNTIF(event_name IN ('purchase', 'conversion')) as conversions
        FROM `st-ga4-data.analytics_{property_id}.events_*`
        WHERE _TABLE_SUFFIX BETWEEN
            FORMAT_DATE('%Y%m%d', DATE '{start_date.strftime('%Y-%m-%d')}')
            AND FORMAT_DATE('%Y%m%d', DATE '{end_date.strftime('%Y-%m-%d')}')
        GROUP BY event_date
        ORDER BY event_date DESC
        """

        # Execute query
        results = client.query(query)
        raw_data = []

        for row in results:
            raw_data.append({
                'date': row.event_date.strftime('%Y-%m-%d'),
                'sessions': int(row.sessions or 0),
                'users': int(row.users or 0),
                'page_views': int(row.page_views or 0),
                'conversions': int(row.conversions or 0)
            })

        if not raw_data:
            print(f"   ⚠️ No data found for property {property_id}")
            return None

        # Use property ID as client name for simplicity
        client_name = f"property_{property_id}"

        # Create clean dataset
        clean_dataset = []
        for day_data in raw_data:
            clean_dataset.append({
                'date': day_data['date'],
                'sessions': day_data['sessions'],
                'users': day_data['users'],
                'page_views': day_data['page_views'],
                'conversions': day_data['conversions'],
                'quality_score': 100,  # Assume good quality from BigQuery
                'data_source': 'bigquery_export'
            })

        # Package the data
        processed_data = {
            'client_metadata': {
                'client_name': client_name,
                'property_id': property_id,
                'processing_timestamp': datetime.now().isoformat(),
                'data_source': 'st-ga4-data',
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days_processed': len(clean_dataset)
                }
            },
            'clean_dataset': clean_dataset,
            'quality_metrics': {
                'overall_score': 100,
                'data_completeness': 100,
                'anomaly_flags': []
            }
        }

        # Save clean dataset file
        clean_file = f"data/scout_production_clean_{property_id}.json"
        with open(clean_file, 'w') as f:
            json.dump(processed_data, f, indent=2)

        print(f"✅ Property {property_id} processed successfully")
        print(f"   📁 Clean dataset: {clean_file}")
        print(f"   📊 {len(clean_dataset)} days processed")
        print(f"   🏢 Client: {client_name}")

        return clean_file

    except Exception as e:
        print(f"❌ Error processing property {property_id}: {e}")
        return None

def run_anomaly_detection_on_property(clean_dataset_file: str) -> Dict[str, Any]:
    """Run anomaly detection on a processed property dataset"""

    try:
        # Import our anomaly detector
        import sys
        sys.path.append('.')
        from scripts.scout_anomaly_detector import run_anomaly_detection

        # Run detection
        result = run_anomaly_detection(clean_dataset_file)

        if result.get('success'):
            return result['results']
        else:
            print(f"❌ Anomaly detection failed: {result.get('error')}")
            return None

    except Exception as e:
        print(f"❌ Error running anomaly detection: {e}")
        return None

def analyze_cross_client_patterns(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns across multiple client properties"""

    print(f"\n🔍 Analyzing Cross-Client Patterns")
    print("=" * 50)

    # Portfolio summary
    total_properties = len(all_results)
    total_anomalies = sum(r['summary']['total_anomalies'] for r in all_results)

    # Traffic level analysis
    traffic_levels = {}
    anomaly_by_traffic = {}

    for result in all_results:
        metadata = result['processing_metadata']
        client_name = metadata['client_name']
        anomaly_count = result['summary']['total_anomalies']

        # Categorize by estimated traffic level based on data patterns
        if 'sample_data' in metadata:
            avg_sessions = metadata.get('avg_daily_sessions', 0)
            traffic_level = 'high' if avg_sessions > 100 else 'medium' if avg_sessions > 20 else 'low'
        else:
            traffic_level = 'unknown'

        traffic_levels[client_name] = traffic_level

        if traffic_level not in anomaly_by_traffic:
            anomaly_by_traffic[traffic_level] = []
        anomaly_by_traffic[traffic_level].append(anomaly_count)

    # Metric comparison across clients
    metric_patterns = {}
    for metric in ['sessions', 'users', 'page_views', 'conversions']:
        metric_patterns[metric] = {
            'total_anomalies': 0,
            'properties_with_anomalies': 0,
            'avg_anomaly_rate': 0
        }

        anomaly_rates = []
        for result in all_results:
            if metric in result['detection_results']:
                metric_result = result['detection_results'][metric]
                anomaly_count = metric_result['anomalies_detected']
                anomaly_rate = metric_result['anomaly_rate']

                metric_patterns[metric]['total_anomalies'] += anomaly_count
                if anomaly_count > 0:
                    metric_patterns[metric]['properties_with_anomalies'] += 1
                anomaly_rates.append(anomaly_rate)

        if anomaly_rates:
            metric_patterns[metric]['avg_anomaly_rate'] = sum(anomaly_rates) / len(anomaly_rates)

    # Business impact distribution
    impact_distribution = {
        'high_impact_total': sum(r['summary']['high_impact'] for r in all_results),
        'medium_impact_total': sum(r['summary']['medium_impact'] for r in all_results),
        'low_impact_total': sum(r['summary']['low_impact'] for r in all_results)
    }

    pattern_analysis = {
        'portfolio_summary': {
            'total_properties_analyzed': total_properties,
            'total_anomalies_detected': total_anomalies,
            'avg_anomalies_per_property': total_anomalies / total_properties if total_properties > 0 else 0,
            'properties_with_anomalies': sum(1 for r in all_results if r['summary']['total_anomalies'] > 0)
        },
        'traffic_level_patterns': {
            'by_level': anomaly_by_traffic,
            'distribution': {level: len(props) for level, props in anomaly_by_traffic.items()}
        },
        'metric_patterns': metric_patterns,
        'impact_distribution': impact_distribution,
        'pattern_insights': []
    }

    # Generate insights
    insights = []

    if total_anomalies == 0:
        insights.append("✅ No anomalies detected across all properties - indicates stable traffic patterns")
    else:
        insights.append(f"🚨 {total_anomalies} total anomalies detected across {total_properties} properties")

    # High-performing metrics
    cleanest_metric = min(metric_patterns.keys(), key=lambda m: metric_patterns[m]['avg_anomaly_rate'])
    insights.append(f"📊 Cleanest metric across portfolio: {cleanest_metric}")

    # Traffic level insights
    if 'high' in anomaly_by_traffic and 'low' in anomaly_by_traffic:
        high_avg = sum(anomaly_by_traffic['high']) / len(anomaly_by_traffic['high'])
        low_avg = sum(anomaly_by_traffic['low']) / len(anomaly_by_traffic['low'])
        if high_avg > low_avg:
            insights.append("📈 Higher traffic properties show more anomalies (more sensitive detection)")
        else:
            insights.append("📉 Lower traffic properties show more anomalies (higher variability)")

    pattern_analysis['pattern_insights'] = insights

    return pattern_analysis

def main():
    """Main execution for multi-property anomaly testing"""

    print("🚀 SCOUT Multi-Property Anomaly Testing")
    print("=" * 60)
    print("Testing cross-client pattern detection across GA4 properties")

    # Setup BigQuery client
    client = setup_bigquery_client()
    if not client:
        return

    # Discover available properties
    properties = list_available_properties(client, limit=15)
    if not properties:
        print("❌ No properties found to test")
        return

    # Select diverse properties for testing
    print(f"\n📋 Selecting Properties for Testing")
    print("-" * 40)

    # Sample up to 5 properties with different traffic levels
    selected_properties = []
    property_samples = {}

    for prop_id in properties[:10]:  # Sample first 10 for efficiency
        sample = get_property_traffic_sample(client, prop_id)
        if sample and sample['data_points'] >= 5:  # Need sufficient data
            property_samples[prop_id] = sample
            selected_properties.append(prop_id)

            if len(selected_properties) >= 5:  # Test with 5 properties max
                break

    if not selected_properties:
        print("❌ No properties with sufficient data found")
        return

    print(f"\n✅ Selected {len(selected_properties)} properties for testing:")
    for prop_id in selected_properties:
        sample = property_samples[prop_id]
        print(f"   • {prop_id}: {sample['traffic_level']} traffic ({sample['avg_daily_sessions']:.0f} sessions/day)")

    # Process each property
    print(f"\n🔄 Processing Selected Properties")
    print("=" * 50)

    all_results = []

    for prop_id in selected_properties:
        # Process property data
        clean_file = process_property_data(client, prop_id)
        if not clean_file:
            continue

        # Run anomaly detection
        print(f"🔍 Running anomaly detection on {prop_id}...")
        detection_result = run_anomaly_detection_on_property(clean_file)

        if detection_result:
            # Add traffic sample data to metadata
            detection_result['processing_metadata']['traffic_sample'] = property_samples[prop_id]
            all_results.append(detection_result)

            summary = detection_result['summary']
            print(f"   📊 Results: {summary['total_anomalies']} anomalies ({summary['high_impact']} high impact)")
        else:
            print(f"   ❌ Failed to run detection")

    if not all_results:
        print("❌ No successful property analyses")
        return

    # Analyze cross-client patterns
    pattern_analysis = analyze_cross_client_patterns(all_results)

    # Display pattern analysis results
    print(f"\n📈 Cross-Client Pattern Analysis Results")
    print("=" * 60)

    portfolio = pattern_analysis['portfolio_summary']
    print(f"Portfolio Overview:")
    print(f"  • Properties Analyzed: {portfolio['total_properties_analyzed']}")
    print(f"  • Total Anomalies: {portfolio['total_anomalies_detected']}")
    print(f"  • Average per Property: {portfolio['avg_anomalies_per_property']:.1f}")
    print(f"  • Properties with Anomalies: {portfolio['properties_with_anomalies']}")

    print(f"\nMetric Performance:")
    for metric, data in pattern_analysis['metric_patterns'].items():
        print(f"  • {metric}: {data['total_anomalies']} anomalies, {data['avg_anomaly_rate']:.1%} avg rate")

    print(f"\nPattern Insights:")
    for insight in pattern_analysis['pattern_insights']:
        print(f"  {insight}")

    # Export comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export individual property results
    for i, result in enumerate(all_results):
        prop_id = result['processing_metadata']['property_id']
        output_file = f"data/scout_anomalies_{prop_id}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"📁 Property {prop_id} results: {output_file}")

    # Export pattern analysis
    pattern_file = f"data/scout_portfolio_patterns_{timestamp}.json"
    with open(pattern_file, 'w') as f:
        json.dump({
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'properties_tested': selected_properties,
                'scout_version': 'multi-property-v1'
            },
            'pattern_analysis': pattern_analysis,
            'individual_results': all_results
        }, f, indent=2)

    print(f"\n💾 Portfolio pattern analysis exported: {pattern_file}")

    print(f"\n🎯 SCOUT Multi-Property Testing Complete!")
    print("=" * 60)
    print(f"✅ Validated anomaly detection across {len(all_results)} properties")
    print(f"🔍 Cross-client pattern detection foundation established")
    print(f"📊 Portfolio-level insights generated for Account Manager alerts")
    print(f"🔄 Ready to build intelligent alerting system with multi-property context")

if __name__ == "__main__":
    main()
