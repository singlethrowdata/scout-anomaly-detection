// [R17-R20] Upload detector alerts to Cloud Storage
// → needs: local detector JSON files
// → provides: cloud-storage-detector-data

const { Storage } = require('@google-cloud/storage');
const fs = require('fs');
const path = require('path');

const storage = new Storage({ projectId: 'st-ga4-data' });
const bucket = storage.bucket('scout-results');

const fileMappings = [
  { local: '../data/scout_disaster_alerts.json', remote: 'disaster_alerts.json' },
  { local: '../data/scout_spam_alerts.json', remote: 'spam_alerts.json' },
  { local: '../data/scout_record_alerts.json', remote: 'record_alerts.json' },
  { local: '../data/scout_trend_alerts.json', remote: 'trend_alerts.json' }
];

async function uploadFiles() {
  console.log('🚀 Uploading detector alerts to Cloud Storage...\n');

  for (const mapping of fileMappings) {
    const localPath = path.join(__dirname, mapping.local);

    if (!fs.existsSync(localPath)) {
      console.log(`⚠️  SKIP: ${mapping.remote} (local file not found at ${localPath})`);
      continue;
    }

    try {
      await bucket.upload(localPath, {
        destination: mapping.remote,
        metadata: {
          contentType: 'application/json',
          metadata: {
            uploadedAt: new Date().toISOString(),
            uploadedBy: 'scout-ui-upload-script'
          }
        }
      });
      console.log(`✅ Uploaded: ${mapping.remote}`);
    } catch (error) {
      console.error(`❌ Failed: ${mapping.remote} - ${error.message}`);
    }
  }

  console.log('\n✅ Upload complete!');
}

uploadFiles().catch(console.error);
