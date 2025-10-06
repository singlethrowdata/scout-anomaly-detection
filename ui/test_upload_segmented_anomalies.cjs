// [R14]: Upload segmented anomaly data to Cloud Storage
// → needs: scout_segment_level_anomalies.json
// → provides: Cloud Storage segment-level anomaly data

const { Storage } = require('@google-cloud/storage');
const fs = require('fs');
const path = require('path');

// Initialize Cloud Storage with Application Default Credentials
const storage = new Storage({
  projectId: 'stm-mvp'
});

const bucketName = 'scout-results';
const bucket = storage.bucket(bucketName);

async function uploadSegmentedAnomalies() {
  console.log('🚀 SCOUT Segmented Anomaly Upload');
  console.log('='.repeat(60));

  // Read the segment-level anomalies file
  const localFilePath = path.join(__dirname, '..', 'data', 'scout_segment_level_anomalies.json');

  if (!fs.existsSync(localFilePath)) {
    console.error(`❌ File not found: ${localFilePath}`);
    process.exit(1);
  }

  // Read and parse to verify JSON validity and strip BOM if present
  const rawData = fs.readFileSync(localFilePath, 'utf8');
  const cleanData = rawData.replace(/^\uFEFF/, ''); // Strip BOM
  const anomalyData = JSON.parse(cleanData);

  console.log(`\n📊 Anomaly Data Summary:`);
  console.log(`  Properties analyzed: ${anomalyData.properties_analyzed}`);
  console.log(`  Total anomalies: ${anomalyData.total_anomalies}`);
  console.log(`  Segment types: ${anomalyData.segment_types.join(', ')}`);

  // Count anomalies by segment type
  const deviceCount = anomalyData.anomalies.filter(a => a.segment_type === 'device').length;
  const geoCount = anomalyData.anomalies.filter(a => a.segment_type === 'geography').length;
  const trafficCount = anomalyData.anomalies.filter(a => a.segment_type === 'traffic_source').length;

  console.log(`\n📈 Breakdown:`);
  console.log(`  Device: ${deviceCount}`);
  console.log(`  Geography: ${geoCount}`);
  console.log(`  Traffic Source: ${trafficCount}`);

  // Upload to Cloud Storage
  const destinationPath = 'segment_anomalies.json';
  const file = bucket.file(destinationPath);

  console.log(`\n☁️  Uploading to gs://${bucketName}/${destinationPath}...`);

  await file.save(cleanData, {
    contentType: 'application/json',
    metadata: {
      cacheControl: 'public, max-age=300',
    },
  });

  console.log(`✅ Upload successful!`);
  console.log(`\n🔗 Access URL: https://storage.googleapis.com/${bucketName}/${destinationPath}`);
  console.log(`\n🎯 Next: Update Results.tsx to filter by segment_type`);
}

uploadSegmentedAnomalies()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('❌ Upload failed:', error);
    process.exit(1);
  });
