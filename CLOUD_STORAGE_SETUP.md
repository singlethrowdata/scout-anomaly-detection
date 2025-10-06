# SCOUT Cloud Storage Integration Guide

## Overview
This guide covers setting up Google Cloud Storage as the data bridge between the TanStack frontend and Cloud Run Jobs backend.

## 1. Create Storage Buckets

```bash
# Create buckets for configuration and results
gsutil mb -p stm-mvp -l us-east1 gs://scout-config
gsutil mb -p stm-mvp -l us-east1 gs://scout-results

# Set lifecycle rules to auto-delete old results (optional)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://scout-results
```

## 2. Configure CORS for Frontend Access

```bash
# Create CORS configuration
cat > cors.json << EOF
[
  {
    "origin": ["https://scout.yourdomain.com", "http://localhost:3001"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

# Apply CORS settings
gsutil cors set cors.json gs://scout-config
gsutil cors set cors.json gs://scout-results
```

## 3. Service Account Setup

```bash
# Create service account for Cloud Run Jobs
gcloud iam service-accounts create scout-processor \
  --display-name="SCOUT Anomaly Processor"

# Grant necessary permissions
gcloud projects add-iam-policy-binding stm-mvp \
  --member="serviceAccount:scout-processor@stm-mvp.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding stm-mvp \
  --member="serviceAccount:scout-processor@stm-mvp.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Create key for local development
gcloud iam service-accounts keys create scout-processor-key.json \
  --iam-account=scout-processor@stm-mvp.iam.gserviceaccount.com
```

## 4. Frontend Integration

### Install Google Cloud Storage client
```bash
npm install @google-cloud/storage
```

### Update ConfigTable.tsx to save to Cloud Storage
```typescript
import { Storage } from '@google-cloud/storage';

const storage = new Storage({
  projectId: 'stm-mvp',
  keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS
});

const bucket = storage.bucket('scout-config');

async function saveConfiguration(config: PropertyConfig[]) {
  const file = bucket.file('properties.json');
  await file.save(JSON.stringify(config), {
    contentType: 'application/json',
    metadata: {
      updated: new Date().toISOString(),
      updatedBy: 'scout-ui'
    }
  });
}
```

## 5. Python Script Updates

### Update scout_anomaly_detector.py
```python
from google.cloud import storage
import json

def load_config_from_gcs():
    """Load property configuration from Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket('scout-config')
    blob = bucket.blob('properties.json')

    if blob.exists():
        config_data = blob.download_as_text()
        return json.loads(config_data)
    return {"configured": []}

def save_results_to_gcs(results):
    """Save anomaly results to Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket('scout-results')

    # Save main results
    blob = bucket.blob('anomalies.json')
    blob.upload_from_string(
        json.dumps(results),
        content_type='application/json'
    )

    # Archive with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_blob = bucket.blob(f'archive/{timestamp}_anomalies.json')
    archive_blob.upload_from_string(
        json.dumps(results),
        content_type='application/json'
    )
```

## 6. Dockerfile for Cloud Run

```dockerfile
FROM python:3.11-slim

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY scripts/ ./scripts/
COPY data/scout_client_config.csv ./data/

# Set environment variables
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/scout-processor-key.json
ENV PYTHONUNBUFFERED=1

# Run the anomaly detection script
CMD ["python", "scripts/scout_anomaly_detector.py"]
```

## 7. Deploy to Cloud Run

```bash
# Build and push container
gcloud builds submit --tag gcr.io/stm-mvp/scout-processor .

# Create Cloud Run Job
gcloud run jobs create scout-anomaly-detection \
  --image gcr.io/stm-mvp/scout-processor \
  --region us-east1 \
  --parallelism 1 \
  --task-timeout 30m \
  --max-retries 2 \
  --service-account scout-processor@stm-mvp.iam.gserviceaccount.com

# Create Cloud Scheduler job
gcloud scheduler jobs create http scout-daily-trigger \
  --location us-east1 \
  --schedule "0 6 * * *" \
  --time-zone "America/New_York" \
  --uri "https://us-east1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/stm-mvp/jobs/scout-anomaly-detection:run" \
  --http-method POST \
  --oauth-service-account-email scout-processor@stm-mvp.iam.gserviceaccount.com
```

## 8. Testing

### Test Cloud Storage Access
```python
# test_cloud_storage.py
from google.cloud import storage
import json

def test_storage_access():
    client = storage.Client()

    # Test config bucket
    config_bucket = client.bucket('scout-config')
    test_config = {"test": True, "timestamp": "2025-10-01"}
    blob = config_bucket.blob('test.json')
    blob.upload_from_string(json.dumps(test_config))
    print("✅ Config bucket write successful")

    # Test results bucket
    results_bucket = client.bucket('scout-results')
    test_results = {"anomalies": [], "timestamp": "2025-10-01"}
    blob = results_bucket.blob('test.json')
    blob.upload_from_string(json.dumps(test_results))
    print("✅ Results bucket write successful")

if __name__ == "__main__":
    test_storage_access()
```

## 9. Frontend Environment Variables

Create `.env.production`:
```env
VITE_GCS_CONFIG_BUCKET=scout-config
VITE_GCS_RESULTS_BUCKET=scout-results
VITE_GCP_PROJECT_ID=stm-mvp
```

## 10. Cost Estimates

Monthly costs for 50 properties:
- Cloud Storage: ~$1 (JSON files < 100MB)
- Cloud Run Jobs: ~$5 (30 min daily)
- Cloud Scheduler: Free (1 job)
- Network egress: ~$2 (UI reads)
- **Total Storage/Compute**: ~$8/month

## Next Steps

1. ✅ Update ConfigTable.tsx to save to Cloud Storage
2. ⬜ Deploy frontend to Vercel with env vars
3. ⬜ Create Dockerfile and build container
4. ⬜ Deploy Cloud Run Job
5. ⬜ Set up Cloud Scheduler
6. ⬜ Test end-to-end pipeline
7. ⬜ Add results dashboard to UI
