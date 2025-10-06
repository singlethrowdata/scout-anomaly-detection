#!/usr/bin/env python3
"""
SCOUT Real Data Connection Test
Tests actual connection to GA4 Property 249571600 and st-ga4-data BigQuery project

[R4]: Data validation and quality checks with real data
→ needs: schema-registry, service account access
→ provides: clean-data (production)
"""

import os
import json
from datetime import datetime, timedelta

def test_environment_setup():
    """Test if environment is properly configured"""
    print("🔧 Testing Environment Setup")
    print("-" * 40)

    # Check for service account info
    service_account = "stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com"
    project_id = "st-ga4-data"
    property_id = "249571600"

    print(f"✓ Service Account: {service_account}")
    print(f"✓ BigQuery Project: {project_id}")
    print(f"✓ GA4 Property: {property_id}")

    # Check if credentials are available
    cred_paths = [
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
        './scout-credentials.json',
        f'./{service_account}.json'
    ]

    credentials_found = False
    for cred_path in cred_paths:
        if cred_path and os.path.exists(cred_path):
            print(f"✓ Credentials found: {cred_path}")
            credentials_found = True
            break

    if not credentials_found:
        print("⚠️ No credentials file found. Will try default authentication.")

    return {
        'service_account': service_account,
        'project_id': project_id,
        'property_id': property_id,
        'credentials_available': credentials_found
    }

def test_bigquery_connection(project_id):
    """Test BigQuery connection and look for GA4 export data"""
    print("\n📊 Testing BigQuery Connection")
    print("-" * 40)

    try:
        from google.cloud import bigquery

        # Initialize client
        client = bigquery.Client(project=project_id)
        print(f"✓ BigQuery client initialized for project: {project_id}")

        # List datasets
        datasets = list(client.list_datasets())
        print(f"✓ Found {len(datasets)} datasets")

        # Look for GA4 export datasets
        ga4_datasets = []
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            print(f"  - {dataset_id}")
            if 'analytics' in dataset_id.lower():
                ga4_datasets.append(dataset_id)

        print(f"✓ Potential GA4 datasets: {ga4_datasets}")

        # Test query on one dataset if available
        if ga4_datasets:
            test_dataset = ga4_datasets[0]
            query = f"""
                SELECT table_name, creation_time
                FROM `{project_id}.{test_dataset}.INFORMATION_SCHEMA.TABLES`
                WHERE table_name LIKE 'events_%'
                LIMIT 5
            """

            try:
                results = client.query(query).result()
                tables = [(row.table_name, row.creation_time) for row in results]
                print(f"✓ Found {len(tables)} GA4 event tables in {test_dataset}")
                for table_name, created in tables[:3]:
                    print(f"  - {table_name} (created: {created.date()})")
                return {'success': True, 'datasets': ga4_datasets, 'sample_tables': tables}
            except Exception as e:
                print(f"⚠️ Could not query tables: {e}")
                return {'success': False, 'error': str(e), 'datasets': ga4_datasets}
        else:
            return {'success': False, 'error': 'No GA4 datasets found', 'datasets': []}

    except ImportError:
        print("❌ google-cloud-bigquery not installed")
        return {'success': False, 'error': 'Missing BigQuery dependency'}
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        return {'success': False, 'error': str(e)}

def test_ga4_api_connection(property_id):
    """Test GA4 Reporting API connection"""
    print("\n📈 Testing GA4 API Connection")
    print("-" * 40)

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

        # Initialize client
        client = BetaAnalyticsDataClient()
        print("✓ GA4 API client initialized")

        # Simple test request - last 7 days
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews")
            ],
            dimensions=[Dimension(name="date")]
        )

        response = client.run_report(request=request)
        print(f"✓ GA4 API request successful")
        print(f"✓ Retrieved {len(response.rows)} days of data")

        # Parse sample data
        sample_data = []
        for row in response.rows[:5]:  # First 5 days
            date_val = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value) if row.metric_values[0].value else 0
            users = int(row.metric_values[1].value) if row.metric_values[1].value else 0
            pageviews = int(row.metric_values[2].value) if row.metric_values[2].value else 0

            sample_data.append({
                'date': date_val,
                'sessions': sessions,
                'users': users,
                'pageviews': pageviews,
                'source': 'ga4_api'
            })
            print(f"  - {date_val}: {sessions:,} sessions, {users:,} users, {pageviews:,} pageviews")

        return {'success': True, 'data': sample_data}

    except ImportError:
        print("❌ google-analytics-data not installed")
        return {'success': False, 'error': 'Missing GA4 API dependency'}
    except Exception as e:
        print(f"❌ GA4 API connection failed: {e}")
        return {'success': False, 'error': str(e)}

def create_real_clean_dataset(bigquery_result, ga4_result):
    """Create clean dataset from real data sources"""
    print("\n✨ Creating Real Clean Dataset")
    print("-" * 40)

    if not bigquery_result.get('success') and not ga4_result.get('success'):
        print("❌ Cannot create clean dataset - both data sources failed")
        return {'success': False, 'error': 'No data sources available'}

    # For now, use GA4 API data as primary (since BigQuery structure is unknown)
    if ga4_result.get('success'):
        ga4_data = ga4_result['data']

        # Create clean dataset using SCOUT logic
        clean_data = []
        for row in ga4_data:
            clean_row = {
                'date': row['date'],
                'sessions': row['sessions'],
                'users': row['users'],
                'pageviews': row['pageviews'],
                'data_quality_score': calculate_real_quality_score(row),
                'cleaned_timestamp': datetime.now().isoformat(),
                'source_mix': 'ga4_api_primary',
                'property_id': '249571600'
            }
            clean_data.append(clean_row)

        # Export clean dataset
        output_data = {
            'clean_dataset': clean_data,
            'source_decisions': {
                'sessions': 'ga4_api (primary data source)',
                'users': 'ga4_api (primary data source)',
                'pageviews': 'ga4_api (primary data source)'
            },
            'validation_results': {
                'bigquery_available': bigquery_result.get('success', False),
                'ga4_api_available': ga4_result.get('success', False),
                'data_source_used': 'ga4_api'
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'property_id': '249571600',
                'records_processed': len(clean_data),
                'avg_quality_score': sum(row['data_quality_score'] for row in clean_data) / len(clean_data),
                'ready_for_anomaly_detection': True
            }
        }

        with open('data/scout_real_clean_data.json', 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Real clean dataset created: {len(clean_data)} records")
        print(f"✅ Average quality score: {output_data['metadata']['avg_quality_score']:.1f}/100")
        print(f"✅ Exported to: data/scout_real_clean_data.json")

        return {'success': True, 'dataset': clean_data, 'metadata': output_data['metadata']}

    else:
        print("❌ GA4 API data not available for clean dataset creation")
        return {'success': False, 'error': 'GA4 API data required'}

def calculate_real_quality_score(row):
    """Calculate quality score for real data row"""
    score = 100

    # Penalize for missing/zero values
    if row['sessions'] == 0:
        score -= 20
    if row['users'] == 0:
        score -= 20
    if row['pageviews'] == 0:
        score -= 10

    # Check data relationships
    if row['sessions'] > 0 and row['users'] > 0:
        session_user_ratio = row['sessions'] / row['users']
        if session_user_ratio < 0.5 or session_user_ratio > 10:
            score -= 15

    return max(score, 0)

def main():
    """Main test execution"""
    print("🚀 SCOUT Real Data Connection Test")
    print("=" * 60)
    print("Property ID: 249571600")
    print("BigQuery Project: st-ga4-data")
    print("Service Account: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com")

    # Test environment setup
    env_config = test_environment_setup()

    # Test BigQuery connection
    bigquery_result = test_bigquery_connection(env_config['project_id'])

    # Test GA4 API connection
    ga4_result = test_ga4_api_connection(env_config['property_id'])

    # Create clean dataset if possible
    clean_result = create_real_clean_dataset(bigquery_result, ga4_result)

    # Final summary
    print("\n🎯 SCOUT Real Data Test Summary")
    print("=" * 60)

    if clean_result.get('success'):
        print("✅ SCOUT data validation system working with real data!")
        print(f"✅ Processed {len(clean_result['dataset'])} days of real GA4 data")
        print(f"✅ Quality score: {clean_result['metadata']['avg_quality_score']:.1f}/100")
        print("✅ Clean dataset ready for anomaly detection")
        print("\n🔄 Next Step: Build anomaly detection engine using this clean data")
    else:
        print("❌ SCOUT data validation system needs access configuration")
        print("📋 Required:")
        print("  1. Service account access to st-ga4-data BigQuery project")
        print("  2. Service account access to GA4 property 249571600")
        print("  3. Credentials file in project directory")

if __name__ == "__main__":
    main()
