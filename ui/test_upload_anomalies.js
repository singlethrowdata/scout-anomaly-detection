// [R9] Test script to upload sample anomaly data to Cloud Storage
// → needs: proxy-server-running
// → provides: anomaly-results-test-data

const testAnomalies = {
  generated_at: new Date().toISOString(),
  properties_analyzed: 2,
  total_anomalies: 8,
  critical_anomalies: 3,
  warning_anomalies: 5,
  anomalies: [
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      date: "2025-10-01",
      metric: "sessions",
      value: "156",
      direction: "drop",
      priority: "critical",
      business_impact: 42,
      z_score: -3.2,
      baseline_mean: 245,
      baseline_stdev: 28,
      detection_methods: "z_score, iqr"
    },
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      date: "2025-10-01",
      metric: "conversions",
      value: "3",
      direction: "drop",
      priority: "critical",
      business_impact: 67,
      z_score: -2.8,
      baseline_mean: 12,
      baseline_stdev: 3.2,
      detection_methods: "z_score"
    },
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      date: "2025-09-30",
      metric: "bounce_rate",
      value: "78%",
      direction: "spike",
      priority: "warning",
      business_impact: 28,
      z_score: 2.3,
      baseline_mean: 52,
      baseline_stdev: 8.5,
      detection_methods: "z_score"
    },
    {
      property_id: "310145509",
      domain: "homeschoolacademy.com",
      date: "2025-10-01",
      metric: "page_views",
      value: "892",
      direction: "spike",
      priority: "warning",
      business_impact: 18,
      z_score: 2.1,
      baseline_mean: 652,
      baseline_stdev: 95,
      detection_methods: "iqr"
    },
    {
      property_id: "310145509",
      domain: "homeschoolacademy.com",
      date: "2025-09-30",
      metric: "users",
      value: "234",
      direction: "spike",
      priority: "warning",
      business_impact: 15,
      z_score: 2.0,
      baseline_mean: 178,
      baseline_stdev: 28,
      detection_methods: "z_score"
    },
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      date: "2025-09-29",
      metric: "avg_session_duration",
      value: "42s",
      direction: "drop",
      priority: "warning",
      business_impact: 12,
      z_score: -2.1,
      baseline_mean: 68,
      baseline_stdev: 12,
      detection_methods: "z_score"
    },
    {
      property_id: "310145509",
      domain: "homeschoolacademy.com",
      date: "2025-09-29",
      metric: "sessions",
      value: "512",
      direction: "spike",
      priority: "critical",
      business_impact: 35,
      z_score: 3.4,
      baseline_mean: 342,
      baseline_stdev: 48,
      detection_methods: "z_score, iqr"
    },
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      date: "2025-09-28",
      metric: "conversions",
      value: "8",
      direction: "drop",
      priority: "warning",
      business_impact: 25,
      z_score: -2.2,
      baseline_mean: 12,
      baseline_stdev: 1.8,
      detection_methods: "z_score"
    }
  ],
  property_stats: [
    {
      property_id: "249571600",
      domain: "singlethrow.com",
      anomalies_count: 5,
      critical: 2,
      warning: 3
    },
    {
      property_id: "310145509",
      domain: "homeschoolacademy.com",
      anomalies_count: 3,
      critical: 1,
      warning: 2
    }
  ]
};

console.log('📤 Uploading anomaly test data to Cloud Storage...');

fetch('http://localhost:5000/api/results/anomalies', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(testAnomalies)
})
  .then(res => res.json())
  .then(data => {
    console.log('✅ Upload successful:', data);
    console.log('\n📊 Test data summary:');
    console.log(`   - Properties: ${testAnomalies.properties_analyzed}`);
    console.log(`   - Total anomalies: ${testAnomalies.total_anomalies}`);
    console.log(`   - Critical: ${testAnomalies.critical_anomalies}`);
    console.log(`   - Warnings: ${testAnomalies.warning_anomalies}`);
    console.log('\n🌐 Navigate to http://localhost:5179/results to view the dashboard');

    // Verify by fetching back
    return fetch('http://localhost:5000/api/results/anomalies');
  })
  .then(res => res.json())
  .then(data => {
    console.log('\n✅ Verification: Data successfully retrieved from Cloud Storage');
    console.log(`   Retrieved ${data.anomalies?.length || 0} anomalies`);
  })
  .catch(err => {
    console.error('❌ Test failed:', err);
  });
