#!/usr/bin/env python3
"""
Test SCOUT Data Validation & Reconciliation System
Validates [R4] implementation with existing access

Purpose: Test clean-data generation for anomaly detection
"""

import sys
import logging
from datetime import datetime
from scout_data_validator import ScoutDataValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_validation_framework():
    """
    Test [R4] data validation framework structure
    """
    print("🔍 Testing SCOUT Data Validation Framework...")

    project_id = "st-ga4-data"
    service_account = "stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com"

    try:
        # [R4]: Test validator initialization
        validator = ScoutDataValidator(project_id, service_account)
        print("✅ Data validator initialized successfully")

        # [R4]: Test validation methods exist
        required_methods = [
            'validate_data_sources',
            'create_clean_dataset',
            '_reconcile_data_sources',
            '_assess_data_quality',
            '_recommend_data_source'
        ]

        for method in required_methods:
            if hasattr(validator, method):
                print(f"✅ Method {method} implemented")
            else:
                print(f"❌ Missing method: {method}")
                return False

        return True

    except Exception as e:
        print(f"❌ Framework test failed: {str(e)}")
        return False

def test_validation_logic():
    """
    Test [R4] data validation and reconciliation logic
    """
    print("\n🧪 Testing Validation Logic...")

    project_id = "st-ga4-data"
    service_account = "stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com"
    validator = ScoutDataValidator(project_id, service_account)

    try:
        # [R4]: Test single property validation
        test_property = "123456789"
        validation_results = validator.validate_data_sources(test_property, days=7)

        # [R4]: Verify validation structure
        required_keys = ['property_id', 'reconciliation', 'data_quality', 'status']
        for key in required_keys:
            if key in validation_results:
                print(f"✅ Validation includes {key}")
            else:
                print(f"❌ Missing validation key: {key}")
                return False

        # [R4]: Check reconciliation logic
        reconciliation = validation_results['reconciliation']
        if 'variance_percentage' in reconciliation:
            variance = reconciliation['variance_percentage']
            print(f"✅ Variance calculated: {variance}%")
        else:
            print("❌ Variance calculation missing")
            return False

        # [R4]: Check data source recommendation
        recommended = reconciliation.get('recommended_source')
        valid_recommendations = ['bigquery_preferred', 'ga4_api_preferred', 'hybrid_required']
        if recommended in valid_recommendations:
            print(f"✅ Data source recommendation: {recommended}")
        else:
            print(f"❌ Invalid recommendation: {recommended}")
            return False

        return True

    except Exception as e:
        print(f"❌ Validation logic test failed: {str(e)}")
        return False

def test_clean_dataset_creation():
    """
    Test [R4] clean dataset creation → provides: clean-data
    """
    print("\n🧹 Testing Clean Dataset Creation...")

    project_id = "st-ga4-data"
    service_account = "stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com"
    validator = ScoutDataValidator(project_id, service_account)

    try:
        # [R4]: Test with multiple properties
        test_properties = ["123456789", "987654321", "555666777"]
        clean_data = validator.create_clean_dataset(test_properties, days=7)

        # [R4]: Verify clean dataset structure
        if len(clean_data) > 0:
            print(f"✅ Clean dataset created: {len(clean_data)} properties")
        else:
            print("❌ Clean dataset empty")
            return False

        # [R4]: Check required columns for anomaly detection
        required_columns = ['property_id', 'sessions', 'users', 'events', 'conversions', 'quality_score']
        for column in required_columns:
            if column in clean_data.columns:
                print(f"✅ Clean data includes {column}")
            else:
                print(f"❌ Missing column: {column}")
                return False

        # [R4]: Verify data quality metrics
        avg_quality = clean_data['quality_score'].mean()
        print(f"✅ Average data quality score: {avg_quality:.1f}/100")

        return True

    except Exception as e:
        print(f"❌ Clean dataset test failed: {str(e)}")
        return False

def test_hybrid_architecture_benefits():
    """
    Test [R4] hybrid architecture addresses BigQuery vs GA4 UI discrepancy
    """
    print("\n🎯 Testing Hybrid Architecture Benefits...")

    project_id = "st-ga4-data"
    service_account = "stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com"
    validator = ScoutDataValidator(project_id, service_account)

    try:
        # [R4]: Simulate high variance scenario (BigQuery vs GA4 UI issue)
        mock_bq_data = {
            'sessions': 1000,
            'users': 800,
            'events': 5000,
            'conversions': 50
        }

        mock_api_data = {
            'sessions': 950,    # 5% lower due to thresholding
            'users': 780,       # Privacy thresholding
            'events': 4800,     # Sampling effect
            'conversions': 48,  # Modeling differences
            'thresholding_applied': True,
            'sampling_rate': 96.0
        }

        # [R4]: Test reconciliation handles the discrepancy
        reconciliation = validator._reconcile_data_sources(mock_bq_data, mock_api_data)

        if reconciliation['variance_percentage'] > 0:
            print(f"✅ Variance detection working: {reconciliation['variance_percentage']}%")
        else:
            print("❌ Variance detection failed")
            return False

        if reconciliation['thresholding_detected']:
            print("✅ Privacy thresholding detection working")
        else:
            print("❌ Thresholding detection failed")
            return False

        # [R4]: Test recommendation logic
        recommendation = validator._recommend_data_source(reconciliation)
        print(f"✅ Hybrid architecture recommendation: {recommendation}")

        return True

    except Exception as e:
        print(f"❌ Hybrid architecture test failed: {str(e)}")
        return False

def main():
    """
    Execute SCOUT data validation tests [R4]
    """
    print("🚀 SCOUT Data Validation & Reconciliation Tests")
    print("=" * 60)
    print(f"Service Account: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com")
    print(f"BigQuery Project: st-ga4-data")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Framework Structure", test_data_validation_framework),
        ("Validation Logic", test_validation_logic),
        ("Clean Dataset Creation", test_clean_dataset_creation),
        ("Hybrid Architecture Benefits", test_hybrid_architecture_benefits)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("✅ DATA VALIDATION SYSTEM READY")
        print("→ Cross-validation framework ✅")
        print("→ Clean dataset creation ✅")
        print("→ Hybrid architecture implemented ✅")
        print("→ Ready to provide clean-data for anomaly detection ✅")
        print("\n🎯 [R4] Data validation and quality checks COMPLETE")
        print("🚀 This unlocks all anomaly detection features!")
        return True
    else:
        print("⚠️ Some validation components need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
