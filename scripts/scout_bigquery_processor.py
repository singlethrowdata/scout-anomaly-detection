#!/usr/bin/env python3
"""
SCOUT BigQuery Data Processor
Processes real GA4 export data from st-ga4-data project

[R4]: Data validation and quality checks with real BigQuery data
→ needs: schema-registry, bigquery access, cloud-storage-config
→ provides: clean-data (production)
"""

import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

def extract_ga4_data(property_id="249571600", days_back=7):
    """Extract GA4 data from BigQuery for specified property and date range"""

    print(f"🔍 Extracting GA4 Data for Property {property_id}")
    print("-" * 50)

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project="st-ga4-data")
        dataset_name = f"analytics_{property_id}"

        # Get date range for recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # [R4]: Enhanced query to extract segmented data for all detector dimensions
        # → provides: Overall + Geography + Devices + Traffic Source + Landing Pages
        query = f"""
        WITH daily_metrics AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                COUNT(DISTINCT user_pseudo_id) as users,
                COUNTIF(event_name = 'session_start') as sessions,
                COUNT(event_name) as total_events,
                COUNTIF(event_name = 'page_view') as page_views,
                COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions,
                -- Quality signals for spam detection
                SAFE_DIVIDE(
                    COUNTIF(event_name = 'user_engagement' AND
                           (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') < 10000),
                    COUNTIF(event_name = 'session_start')
                ) as bounce_rate,
                SAFE_DIVIDE(
                    SUM(CASE WHEN event_name = 'user_engagement'
                        THEN (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec')
                        ELSE 0 END),
                    COUNTIF(event_name = 'session_start') * 1000
                ) as avg_session_duration
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
            GROUP BY event_date
        ),
        -- Geography segments (for Spam and Trend detectors)
        geo_segments AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                geo.country as country,
                COUNT(DISTINCT user_pseudo_id) as users,
                COUNTIF(event_name = 'session_start') as sessions,
                COUNTIF(event_name = 'page_view') as page_views,
                COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions,
                SAFE_DIVIDE(
                    COUNTIF(event_name = 'user_engagement' AND
                           (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') < 10000),
                    COUNTIF(event_name = 'session_start')
                ) as bounce_rate,
                SAFE_DIVIDE(
                    SUM(CASE WHEN event_name = 'user_engagement'
                        THEN (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec')
                        ELSE 0 END),
                    COUNTIF(event_name = 'session_start') * 1000
                ) as avg_session_duration
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
              AND geo.country IS NOT NULL
            GROUP BY event_date, geo.country
            HAVING sessions >= 10  -- Minimum volume filter
        ),
        -- Device segments (for Record and Trend detectors)
        device_segments AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                device.category as device_category,
                COUNT(DISTINCT user_pseudo_id) as users,
                COUNTIF(event_name = 'session_start') as sessions,
                COUNTIF(event_name = 'page_view') as page_views,
                COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
              AND device.category IS NOT NULL
            GROUP BY event_date, device.category
            HAVING sessions >= 10  -- Minimum volume filter
        ),
        -- Traffic source segments (for Spam, Record, and Trend detectors)
        traffic_segments AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                traffic_source.source as source,
                traffic_source.medium as medium,
                COUNT(DISTINCT user_pseudo_id) as users,
                COUNTIF(event_name = 'session_start') as sessions,
                COUNTIF(event_name = 'page_view') as page_views,
                COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions,
                SAFE_DIVIDE(
                    COUNTIF(event_name = 'user_engagement' AND
                           (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') < 10000),
                    COUNTIF(event_name = 'session_start')
                ) as bounce_rate,
                SAFE_DIVIDE(
                    SUM(CASE WHEN event_name = 'user_engagement'
                        THEN (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec')
                        ELSE 0 END),
                    COUNTIF(event_name = 'session_start') * 1000
                ) as avg_session_duration
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
              AND traffic_source.source IS NOT NULL
              AND traffic_source.medium IS NOT NULL
            GROUP BY event_date, traffic_source.source, traffic_source.medium
            HAVING sessions >= 10  -- Minimum volume filter
        ),
        -- Landing page segments (for Record and Trend detectors)
        page_segments AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location' LIMIT 1) as landing_page,
                COUNT(DISTINCT user_pseudo_id) as users,
                COUNTIF(event_name = 'session_start') as sessions,
                COUNTIF(event_name = 'page_view') as page_views,
                COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
              AND event_name = 'session_start'  -- Only session starts for landing pages
            GROUP BY event_date, landing_page
            HAVING sessions >= 10  -- Minimum volume filter
            ORDER BY sessions DESC
            LIMIT 20  -- Top 20 landing pages per day
        ),
        domain_info AS (
            SELECT
                (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location' LIMIT 1) as page_url,
                COUNT(*) as url_frequency
            FROM `st-ga4-data.{dataset_name}.events_*`
            WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY))
                  AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
              AND event_name = 'page_view'
              AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') IS NOT NULL
            GROUP BY page_url
            ORDER BY url_frequency DESC
            LIMIT 10
        )
        SELECT
            'daily_metrics' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                date,
                users,
                sessions,
                total_events,
                page_views,
                conversions,
                bounce_rate,
                avg_session_duration
            ) ORDER BY date DESC)) as data
        FROM daily_metrics

        UNION ALL

        SELECT
            'geo_segments' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                date,
                country,
                users,
                sessions,
                page_views,
                conversions,
                bounce_rate,
                avg_session_duration
            ) ORDER BY date DESC, sessions DESC)) as data
        FROM geo_segments

        UNION ALL

        SELECT
            'device_segments' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                date,
                device_category,
                users,
                sessions,
                page_views,
                conversions
            ) ORDER BY date DESC, sessions DESC)) as data
        FROM device_segments

        UNION ALL

        SELECT
            'traffic_segments' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                date,
                source,
                medium,
                users,
                sessions,
                page_views,
                conversions,
                bounce_rate,
                avg_session_duration
            ) ORDER BY date DESC, sessions DESC)) as data
        FROM traffic_segments

        UNION ALL

        SELECT
            'page_segments' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                date,
                landing_page,
                users,
                sessions,
                page_views,
                conversions
            ) ORDER BY date DESC, sessions DESC)) as data
        FROM page_segments

        UNION ALL

        SELECT
            'domain_info' as data_type,
            TO_JSON_STRING(ARRAY_AGG(STRUCT(
                page_url,
                url_frequency
            ) ORDER BY url_frequency DESC)) as data
        FROM domain_info
        """

        print(f"Querying dataset: {dataset_name}")
        print(f"Date range: {start_date.date()} to {end_date.date()}")

        query_job = client.query(query)
        results = query_job.result()

        # Parse results
        daily_data = []
        geo_data = []
        device_data = []
        traffic_data = []
        page_data = []
        domain_data = []

        for row in results:
            if row.data_type == 'daily_metrics':
                daily_data = json.loads(row.data)
            elif row.data_type == 'geo_segments':
                geo_data = json.loads(row.data)
            elif row.data_type == 'device_segments':
                device_data = json.loads(row.data)
            elif row.data_type == 'traffic_segments':
                traffic_data = json.loads(row.data)
            elif row.data_type == 'page_segments':
                page_data = json.loads(row.data)
            elif row.data_type == 'domain_info':
                domain_data = json.loads(row.data)

        print(f"✅ Retrieved {len(daily_data)} days of metrics")
        print(f"✅ Retrieved {len(geo_data)} geography segments")
        print(f"✅ Retrieved {len(device_data)} device segments")
        print(f"✅ Retrieved {len(traffic_data)} traffic source segments")
        print(f"✅ Retrieved {len(page_data)} landing page segments")
        print(f"✅ Retrieved {len(domain_data)} domain samples")

        return {
            'success': True,
            'property_id': property_id,
            'daily_metrics': daily_data,
            'geo_segments': geo_data,
            'device_segments': device_data,
            'traffic_segments': traffic_data,
            'page_segments': page_data,
            'domain_info': domain_data,
            'date_range': {
                'start': start_date.date().isoformat(),
                'end': end_date.date().isoformat()
            }
        }

    except Exception as e:
        print(f"❌ BigQuery extraction failed: {e}")
        return {'success': False, 'error': str(e)}

def infer_client_name(domain_data):
    """Infer client name from domain data"""

    if not domain_data:
        return f"client_{property_id}"

    # Get most frequent domain
    top_domain = domain_data[0]['page_url'] if domain_data else None

    if not top_domain:
        return f"client_{property_id}"

    try:
        # Parse domain from URL
        parsed = urlparse(top_domain)
        domain = parsed.netloc.lower()

        # Remove www and common prefixes
        domain = domain.replace('www.', '').replace('shop.', '').replace('store.', '')

        # Extract base domain name (before first dot)
        base_name = domain.split('.')[0] if '.' in domain else domain

        # Clean up common patterns
        base_name = base_name.replace('-', '_').replace(' ', '_')

        print(f"🏷️ Client name inferred: '{base_name}' from domain '{domain}'")

        return base_name

    except Exception as e:
        print(f"⚠️ Could not parse domain from {top_domain}: {e}")
        return f"client_{property_id}"

def validate_data_quality(daily_metrics):
    """Validate quality of extracted data"""

    print("\n🔍 Data Quality Assessment")
    print("-" * 30)

    quality_issues = []
    total_score = 100

    if not daily_metrics:
        return {'score': 0, 'issues': ['No data available']}

    # Check for missing days
    expected_days = 7
    actual_days = len(daily_metrics)
    if actual_days < expected_days * 0.8:  # Allow 20% missing
        quality_issues.append(f"Missing data: {actual_days}/{expected_days} days")
        total_score -= 20

    # Check for zero values
    zero_sessions_days = sum(1 for day in daily_metrics if day['sessions'] == 0)
    if zero_sessions_days > 0:
        quality_issues.append(f"Zero sessions on {zero_sessions_days} days")
        total_score -= (zero_sessions_days * 10)

    # Check data consistency
    for day in daily_metrics:
        if day['sessions'] > 0 and day['users'] > 0:
            session_user_ratio = day['sessions'] / day['users']
            if session_user_ratio < 0.5 or session_user_ratio > 10:
                quality_issues.append(f"Unusual session/user ratio on {day['date']}: {session_user_ratio:.2f}")
                total_score -= 5

    # Check conversion rates
    for day in daily_metrics:
        if day['sessions'] > 0:
            conversion_rate = day['conversions'] / day['sessions']
            if conversion_rate > 0.5:  # >50% conversion suspicious
                quality_issues.append(f"High conversion rate on {day['date']}: {conversion_rate:.1%}")
                total_score -= 5

    final_score = max(total_score, 0)

    print(f"Quality Score: {final_score}/100")
    for issue in quality_issues:
        print(f"  ⚠️ {issue}")

    if not quality_issues:
        print("  ✅ No quality issues detected")

    return {'score': final_score, 'issues': quality_issues}

def create_clean_production_dataset(extraction_result):
    """Create clean dataset ready for anomaly detection"""

    if not extraction_result.get('success'):
        return {'success': False, 'error': 'Data extraction failed'}

    print("\n✨ Creating Clean Production Dataset")
    print("-" * 40)

    property_id = extraction_result['property_id']
    daily_metrics = extraction_result['daily_metrics']
    geo_segments = extraction_result.get('geo_segments', [])
    device_segments = extraction_result.get('device_segments', [])
    traffic_segments = extraction_result.get('traffic_segments', [])
    page_segments = extraction_result.get('page_segments', [])
    domain_data = extraction_result['domain_info']

    # Infer client name
    client_name = infer_client_name(domain_data)

    # Validate data quality
    quality_assessment = validate_data_quality(daily_metrics)

    # Create clean dataset (overall dimension)
    clean_data = []
    for day_data in daily_metrics:
        clean_row = {
            'date': day_data['date'],
            'property_id': property_id,
            'client_name': client_name,
            'sessions': day_data['sessions'],
            'users': day_data['users'],
            'page_views': day_data['page_views'],
            'conversions': day_data['conversions'],
            'total_events': day_data['total_events'],
            'bounce_rate': day_data.get('bounce_rate', 0),
            'avg_session_duration': day_data.get('avg_session_duration', 0),
            'data_quality_score': quality_assessment['score'],
            'source': 'bigquery_export',
            'processed_timestamp': datetime.now().isoformat()
        }
        clean_data.append(clean_row)

    # Create export dataset with all dimensions
    export_data = {
        'clean_dataset': clean_data,
        # [R4]: Segmented data for multi-dimension anomaly detection
        'geo_segments': geo_segments,  # For Spam and Trend detectors
        'device_segments': device_segments,  # For Record and Trend detectors
        'traffic_segments': traffic_segments,  # For Spam, Record, and Trend detectors
        'page_segments': page_segments,  # For Record and Trend detectors
        'client_metadata': {
            'property_id': property_id,
            'client_name': client_name,
            'inferred_domain': domain_data[0]['page_url'] if domain_data else 'unknown',
            'data_source': 'bigquery_export'
        },
        'quality_assessment': quality_assessment,
        'processing_metadata': {
            'created_at': datetime.now().isoformat(),
            'records_processed': len(clean_data),
            'segment_counts': {
                'geo_segments': len(geo_segments),
                'device_segments': len(device_segments),
                'traffic_segments': len(traffic_segments),
                'page_segments': len(page_segments)
            },
            'date_range': extraction_result['date_range'],
            'avg_quality_score': quality_assessment['score'],
            'ready_for_anomaly_detection': quality_assessment['score'] >= 70
        }
    }

    # Export to file
    output_file = f"data/scout_production_clean_{property_id}.json"
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✅ Clean dataset created: {len(clean_data)} records")
    print(f"✅ Geography segments: {len(geo_segments)} records")
    print(f"✅ Device segments: {len(device_segments)} records")
    print(f"✅ Traffic source segments: {len(traffic_segments)} records")
    print(f"✅ Landing page segments: {len(page_segments)} records")
    print(f"✅ Client identified: {client_name}")
    print(f"✅ Quality score: {quality_assessment['score']}/100")
    print(f"✅ Exported to: {output_file}")

    return {
        'success': True,
        'dataset': clean_data,
        'client_name': client_name,
        'quality_score': quality_assessment['score'],
        'output_file': output_file,
        'metadata': export_data['processing_metadata']
    }

def main():
    """Main execution for SCOUT BigQuery processing"""

    print("🚀 SCOUT Production BigQuery Processor")
    print("=" * 60)
    print("Loading configuration from Cloud Storage...")

    # [NEW] Load configured properties from Cloud Storage
    try:
        from google.cloud import storage

        storage_client = storage.Client(project="st-ga4-data")
        bucket = storage_client.bucket("scout-config")
        blob = bucket.blob("properties.json")

        if not blob.exists():
            print("❌ No properties configured in Cloud Storage")
            print("   Please configure properties in the SCOUT UI first")
            return

        config_json = blob.download_as_text()
        config = json.loads(config_json)

        properties = config.get('properties', [])
        configured_properties = [p for p in properties if p.get('is_configured', False)]

        print(f"✅ Loaded {len(configured_properties)} configured properties from Cloud Storage")
        print()

        if not configured_properties:
            print("⚠️ No properties are configured for monitoring")
            print("   Configure properties in the SCOUT UI to begin processing")
            return

    except Exception as e:
        print(f"❌ Failed to load Cloud Storage configuration: {e}")
        print("   Falling back to static property list")
        # Fallback to hardcoded property for backward compatibility
        configured_properties = [{'property_id': '249571600', 'client_name': 'Single Throw Marketing'}]

    # Process each configured property
    all_results = []
    for prop in configured_properties:
        property_id = prop['property_id']
        client_name = prop.get('client_name', f'client_{property_id}')

        print(f"\n{'=' * 60}")
        print(f"Processing Property: {property_id}")
        print(f"Client: {client_name}")
        print(f"Data Source: st-ga4-data BigQuery project")
        print(f"{'=' * 60}")

        # Extract real GA4 data
        extraction_result = extract_ga4_data(property_id, days_back=7)

        if not extraction_result.get('success'):
            print(f"❌ Data extraction failed for {property_id}")
            all_results.append({'property_id': property_id, 'success': False})
            continue

        # Process into clean dataset
        clean_result = create_clean_production_dataset(extraction_result)

        if clean_result.get('success'):
            print(f"✅ Successfully processed {property_id}")
            all_results.append({
                'property_id': property_id,
                'client_name': clean_result['client_name'],
                'success': True,
                'records': len(clean_result['dataset']),
                'quality_score': clean_result['quality_score']
            })
        else:
            print(f"❌ Clean dataset creation failed for {property_id}")
            all_results.append({'property_id': property_id, 'success': False})

    # Final summary
    print("\n🎯 SCOUT BigQuery Processing Complete")
    print("=" * 60)

    successful = [r for r in all_results if r.get('success')]
    failed = [r for r in all_results if not r.get('success')]

    print(f"✅ Successful: {len(successful)}/{len(all_results)} properties")
    for result in successful:
        print(f"   • {result['client_name']} ({result['property_id']}): {result['records']} days, Quality: {result['quality_score']}/100")

    if failed:
        print(f"\n❌ Failed: {len(failed)} properties")
        for result in failed:
            print(f"   • Property {result['property_id']}")

    print("\n🔄 Next Step: Run detector scripts to analyze this production data")
    print("📊 SCOUT now has real clean data from your configured clients!")

if __name__ == "__main__":
    main()
