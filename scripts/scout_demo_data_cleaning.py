#!/usr/bin/env python3
"""
SCOUT Data Cleaning Demonstration
Shows actual data validation and cleaning with mock GA4 data

[R4]: Data validation and quality checks
→ needs: schema-registry
→ provides: clean-data
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def generate_mock_ga4_data():
    """Generate realistic GA4 data with known quality issues for testing"""

    # Mock BigQuery Export Data (what we'd get from BigQuery)
    bigquery_data = {
        'date': ['2024-09-25', '2024-09-26', '2024-09-27', '2024-09-28'],
        'sessions': [1250, 1180, 1340, 1420],
        'users': [980, 920, 1050, 1120],
        'page_views': [3200, 2950, 3450, 3680],
        'conversions': [45, 42, 51, 58],
        'bounce_rate': [0.65, 0.68, 0.62, 0.59],
        'session_duration': [245.3, 238.7, 252.1, 261.4],
        'source': 'bigquery_export'
    }

    # Mock GA4 API Data (what we'd get from GA4 Reporting API)
    # Intentionally different due to sampling/processing differences
    ga4_api_data = {
        'date': ['2024-09-25', '2024-09-26', '2024-09-27', '2024-09-28'],
        'sessions': [1285, 1205, 1370, 1450],  # ~3% higher (sampling difference)
        'users': [995, 940, 1065, 1140],       # ~2% higher
        'page_views': [3280, 3020, 3520, 3760], # ~2.5% higher
        'conversions': [46, 43, 52, 59],       # Close match (critical metric)
        'bounce_rate': [0.63, 0.66, 0.60, 0.57], # Slightly different calculation
        'session_duration': [251.2, 242.8, 258.3, 267.1], # Different aggregation
        'source': 'ga4_api'
    }

    return pd.DataFrame(bigquery_data), pd.DataFrame(ga4_api_data)

def detect_data_quality_issues(df, source_name):
    """Detect common data quality issues in GA4 data"""
    issues = []

    # Check for missing values
    missing_cols = df.isnull().sum()
    if missing_cols.any():
        issues.append(f"Missing values detected in {source_name}: {missing_cols[missing_cols > 0].to_dict()}")

    # Check for negative values where they shouldn't exist
    numeric_cols = ['sessions', 'users', 'page_views', 'conversions']
    for col in numeric_cols:
        if col in df.columns and (df[col] < 0).any():
            issues.append(f"Negative values in {col} for {source_name}")

    # Check for unrealistic bounce rates
    if 'bounce_rate' in df.columns:
        invalid_bounce = (df['bounce_rate'] < 0) | (df['bounce_rate'] > 1)
        if invalid_bounce.any():
            issues.append(f"Invalid bounce rates in {source_name}: {df[invalid_bounce]['bounce_rate'].values}")

    # Check for session/user ratio consistency
    if 'sessions' in df.columns and 'users' in df.columns:
        session_user_ratio = df['sessions'] / df['users']
        if (session_user_ratio > 5).any() or (session_user_ratio < 0.5).any():
            issues.append(f"Unusual session/user ratio in {source_name}")

    return issues

def calculate_variance_between_sources(bq_df, api_df):
    """Calculate variance between BigQuery and GA4 API data sources"""
    variances = {}

    for col in ['sessions', 'users', 'page_views', 'conversions']:
        if col in bq_df.columns and col in api_df.columns:
            # Calculate percentage difference
            variance = ((api_df[col] - bq_df[col]) / bq_df[col] * 100).mean()
            variances[col] = {
                'avg_variance_percent': round(variance, 2),
                'bigquery_total': int(bq_df[col].sum()),
                'ga4_api_total': int(api_df[col].sum()),
                'difference': int(api_df[col].sum() - bq_df[col].sum())
            }

    return variances

def recommend_data_source(variances, metric):
    """Recommend which data source to use for each metric"""
    if metric not in variances:
        return "unknown", "Metric not found in variance analysis"

    variance = variances[metric]
    avg_variance = abs(variance['avg_variance_percent'])

    # Decision logic based on variance patterns
    if metric == 'conversions':
        # Conversions are critical - prefer source with better tracking
        if avg_variance < 5:
            return "ga4_api", f"Low variance ({avg_variance}%) - GA4 API preferred for conversion accuracy"
        else:
            return "hybrid", f"High variance ({avg_variance}%) - requires reconciliation"

    elif metric in ['sessions', 'users']:
        # User metrics - prefer BigQuery for cost efficiency if variance is reasonable
        if avg_variance < 10:
            return "bigquery", f"Acceptable variance ({avg_variance}%) - BigQuery preferred for cost"
        else:
            return "ga4_api", f"High variance ({avg_variance}%) - GA4 API more reliable"

    elif metric == 'page_views':
        # Page views - depends on variance level
        if avg_variance < 5:
            return "bigquery", f"Low variance ({avg_variance}%) - BigQuery sufficient"
        else:
            return "hybrid", f"Moderate variance ({avg_variance}%) - hybrid approach recommended"

    return "bigquery", "Default to BigQuery for cost efficiency"

def create_clean_dataset(bq_df, api_df, variances):
    """Create cleaned dataset using optimal data sources for each metric"""

    clean_data = pd.DataFrame()
    clean_data['date'] = bq_df['date']  # Date is consistent across sources

    source_decisions = {}

    for metric in ['sessions', 'users', 'page_views', 'conversions']:
        source, reason = recommend_data_source(variances, metric)
        source_decisions[metric] = {'source': source, 'reason': reason}

        if source == "bigquery":
            clean_data[metric] = bq_df[metric]
        elif source == "ga4_api":
            clean_data[metric] = api_df[metric]
        elif source == "hybrid":
            # Simple hybrid: average the two sources
            clean_data[metric] = ((bq_df[metric] + api_df[metric]) / 2).round().astype(int)

    # Handle derived metrics (prefer GA4 API for user experience metrics)
    clean_data['bounce_rate'] = api_df['bounce_rate']
    clean_data['session_duration'] = api_df['session_duration']

    # Add metadata
    clean_data['data_quality_score'] = calculate_quality_score(clean_data)
    clean_data['cleaned_timestamp'] = datetime.now().isoformat()

    return clean_data, source_decisions

def calculate_quality_score(df):
    """Calculate data quality score (0-100) for each row"""
    scores = []

    for idx, row in df.iterrows():
        score = 100  # Start with perfect score

        # Penalize for missing data
        missing_penalty = row.isnull().sum() * 10
        score -= missing_penalty

        # Check metric relationships
        if row['sessions'] > 0 and row['users'] > 0:
            session_user_ratio = row['sessions'] / row['users']
            if session_user_ratio < 0.5 or session_user_ratio > 5:
                score -= 15  # Unusual ratio

        # Check conversion rate reasonableness
        if row['sessions'] > 0:
            conversion_rate = row['conversions'] / row['sessions']
            if conversion_rate > 0.2:  # >20% conversion rate is suspicious
                score -= 20

        scores.append(max(score, 0))  # Floor at 0

    return scores

def main():
    """Main demonstration of SCOUT data cleaning process"""

    print("🔍 SCOUT Data Cleaning Demonstration")
    print("=" * 60)

    # Step 1: Generate mock data sources
    print("\n📊 Step 1: Loading Data Sources")
    bq_df, api_df = generate_mock_ga4_data()

    print(f"BigQuery Export Data: {len(bq_df)} rows")
    print(bq_df.head())

    print(f"\nGA4 API Data: {len(api_df)} rows")
    print(api_df.head())

    # Step 2: Data Quality Assessment
    print("\n🔍 Step 2: Data Quality Assessment")
    bq_issues = detect_data_quality_issues(bq_df, "BigQuery")
    api_issues = detect_data_quality_issues(api_df, "GA4 API")

    print(f"BigQuery Issues: {len(bq_issues)}")
    for issue in bq_issues:
        print(f"  - {issue}")

    print(f"GA4 API Issues: {len(api_issues)}")
    for issue in api_issues:
        print(f"  - {issue}")

    if not bq_issues and not api_issues:
        print("✅ No data quality issues detected")

    # Step 3: Variance Analysis
    print("\n📈 Step 3: Cross-Source Variance Analysis")
    variances = calculate_variance_between_sources(bq_df, api_df)

    for metric, variance_data in variances.items():
        print(f"\n{metric.upper()}:")
        print(f"  BigQuery Total: {variance_data['bigquery_total']:,}")
        print(f"  GA4 API Total: {variance_data['ga4_api_total']:,}")
        print(f"  Difference: {variance_data['difference']:,} ({variance_data['avg_variance_percent']:+.1f}%)")

    # Step 4: Data Source Recommendations
    print("\n🎯 Step 4: Data Source Recommendations")
    for metric in variances.keys():
        source, reason = recommend_data_source(variances, metric)
        print(f"{metric}: {source.upper()} - {reason}")

    # Step 5: Create Clean Dataset
    print("\n✨ Step 5: Clean Dataset Creation")
    clean_df, source_decisions = create_clean_dataset(bq_df, api_df, variances)

    print("Clean Dataset:")
    print(clean_df)

    print("\nSource Decision Summary:")
    for metric, decision in source_decisions.items():
        print(f"  {metric}: {decision['source']} - {decision['reason']}")

    # Step 6: Quality Metrics
    print("\n📊 Step 6: Quality Metrics")
    avg_quality_score = clean_df['data_quality_score'].mean()
    print(f"Average Data Quality Score: {avg_quality_score:.1f}/100")

    total_records = len(clean_df)
    high_quality_records = len(clean_df[clean_df['data_quality_score'] >= 90])
    print(f"High Quality Records: {high_quality_records}/{total_records} ({high_quality_records/total_records*100:.1f}%)")

    # Step 7: Export Results
    print("\n💾 Step 7: Export Clean Data")
    output_file = "data/scout_clean_demo.json"

    # Prepare export data
    export_data = {
        'clean_dataset': clean_df.to_dict('records'),
        'source_decisions': source_decisions,
        'variance_analysis': variances,
        'quality_summary': {
            'average_quality_score': avg_quality_score,
            'high_quality_percentage': high_quality_records/total_records*100,
            'total_records': total_records
        },
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'scout_version': '1.0',
            'data_sources': ['bigquery_export', 'ga4_api']
        }
    }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✅ Clean data exported to: {output_file}")

    # Final Summary
    print("\n🎯 SCOUT Data Cleaning Summary")
    print("=" * 60)
    print(f"✅ Processed {total_records} days of GA4 data")
    print(f"✅ Resolved variance issues across {len(variances)} metrics")
    print(f"✅ Achieved {avg_quality_score:.1f}/100 average quality score")
    print(f"✅ Ready for anomaly detection engine")

    return clean_df, source_decisions, variances

if __name__ == "__main__":
    main()
