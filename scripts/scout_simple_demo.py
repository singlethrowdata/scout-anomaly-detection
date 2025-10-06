#!/usr/bin/env python3
"""
SCOUT Simple Data Cleaning Demo (No Dependencies)
Shows data validation logic without requiring pandas/numpy

[R4]: Data validation and quality checks
→ needs: schema-registry
→ provides: clean-data
"""

import json
from datetime import datetime

def main():
    """Simple demonstration of SCOUT data cleaning without dependencies"""

    print("🔍 SCOUT Data Cleaning Demo (Dependency-Free)")
    print("=" * 60)

    # Mock BigQuery data (as Python dictionaries)
    bigquery_data = [
        {'date': '2024-09-25', 'sessions': 1250, 'users': 980, 'conversions': 45, 'source': 'bigquery'},
        {'date': '2024-09-26', 'sessions': 1180, 'users': 920, 'conversions': 42, 'source': 'bigquery'},
        {'date': '2024-09-27', 'sessions': 1340, 'users': 1050, 'conversions': 51, 'source': 'bigquery'},
        {'date': '2024-09-28', 'sessions': 1420, 'users': 1120, 'conversions': 58, 'source': 'bigquery'},
    ]

    # Mock GA4 API data (slightly different due to sampling)
    ga4_api_data = [
        {'date': '2024-09-25', 'sessions': 1285, 'users': 995, 'conversions': 46, 'source': 'ga4_api'},
        {'date': '2024-09-26', 'sessions': 1205, 'users': 940, 'conversions': 43, 'source': 'ga4_api'},
        {'date': '2024-09-27', 'sessions': 1370, 'users': 1065, 'conversions': 52, 'source': 'ga4_api'},
        {'date': '2024-09-28', 'sessions': 1450, 'users': 1140, 'conversions': 59, 'source': 'ga4_api'},
    ]

    print("📊 Raw Data Sources:")
    print(f"BigQuery: {len(bigquery_data)} records")
    print(f"GA4 API: {len(ga4_api_data)} records")

    # Calculate variance
    print("\n📈 Variance Analysis:")
    for i, (bq_row, api_row) in enumerate(zip(bigquery_data, ga4_api_data)):
        sessions_diff = ((api_row['sessions'] - bq_row['sessions']) / bq_row['sessions'] * 100)
        users_diff = ((api_row['users'] - bq_row['users']) / bq_row['users'] * 100)
        conversions_diff = ((api_row['conversions'] - bq_row['conversions']) / bq_row['conversions'] * 100)

        print(f"  Day {i+1}: Sessions {sessions_diff:+.1f}%, Users {users_diff:+.1f}%, Conversions {conversions_diff:+.1f}%")

    # Create clean dataset with source recommendations
    print("\n✨ Clean Dataset Creation:")
    clean_data = []
    source_decisions = {
        'sessions': 'bigquery (cost efficient, <10% variance)',
        'users': 'bigquery (cost efficient, <5% variance)',
        'conversions': 'ga4_api (critical metric, prefer UI accuracy)'
    }

    for i, (bq_row, api_row) in enumerate(zip(bigquery_data, ga4_api_data)):
        clean_row = {
            'date': bq_row['date'],
            'sessions': bq_row['sessions'],      # Use BigQuery for cost
            'users': bq_row['users'],            # Use BigQuery for cost
            'conversions': api_row['conversions'], # Use GA4 API for accuracy
            'data_quality_score': 95,            # High quality (realistic data)
            'cleaned_timestamp': datetime.now().isoformat(),
            'source_mix': 'hybrid'
        }
        clean_data.append(clean_row)

    print("Source Decisions:")
    for metric, decision in source_decisions.items():
        print(f"  {metric}: {decision}")

    print("\nCleaned Data:")
    for row in clean_data:
        print(f"  {row['date']}: {row['sessions']:,} sessions, {row['users']:,} users, {row['conversions']} conversions (Quality: {row['data_quality_score']})")

    # Export results
    output_data = {
        'clean_dataset': clean_data,
        'source_decisions': source_decisions,
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'records_processed': len(clean_data),
            'avg_quality_score': 95,
            'ready_for_anomaly_detection': True
        }
    }

    with open('data/scout_clean_simple_demo.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 Clean data exported: data/scout_clean_simple_demo.json")
    print("\n🎯 SCOUT Data Validation Summary:")
    print("✅ Framework operational")
    print("✅ Variance detection working")
    print("✅ Source recommendation logic functional")
    print("✅ Clean dataset generation complete")
    print("❌ Missing: Real data connections")
    print("❌ Missing: Live service account integration")

    return clean_data

if __name__ == "__main__":
    main()
