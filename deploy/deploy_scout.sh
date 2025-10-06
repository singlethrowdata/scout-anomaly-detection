#!/bin/bash

# SCOUT Production Deployment Script
# Deploys all Cloud Functions and sets up Cloud Scheduler

echo "🚀 SCOUT Production Deployment Starting..."
echo "========================================"

# Configuration
PROJECT_ID="stm-analytics-project"
REGION="us-east1"
SERVICE_ACCOUNT="scout-service@${PROJECT_ID}.iam.gserviceaccount.com"

# Set the project
gcloud config set project ${PROJECT_ID}

echo ""
echo "📦 Step 1: Deploying Main SCOUT Pipeline Function..."
echo "-----------------------------------------------------"

gcloud functions deploy scout-daily-pipeline \
    --gen2 \
    --runtime=python310 \
    --region=${REGION} \
    --source=. \
    --entry-point=scout_daily_pipeline \
    --trigger-http \
    --allow-unauthenticated \
    --memory=1GB \
    --timeout=540s \
    --max-instances=10 \
    --min-instances=0 \
    --service-account=${SERVICE_ACCOUNT} \
    --set-env-vars="GCP_PROJECT=${PROJECT_ID},SCOUT_DATASET=scout_analytics" \
    --set-secrets="GOOGLE_APPLICATION_CREDENTIALS=scout-credentials:latest"

echo ""
echo "📦 Step 2: Deploying Health Check Function..."
echo "---------------------------------------------"

gcloud functions deploy scout-health-check \
    --gen2 \
    --runtime=python310 \
    --region=${REGION} \
    --source=. \
    --entry-point=health_check \
    --trigger-http \
    --allow-unauthenticated \
    --memory=256MB \
    --timeout=60s \
    --max-instances=3

echo ""
echo "⏰ Step 3: Setting up Cloud Scheduler Jobs..."
echo "---------------------------------------------"

# Create Cloud Scheduler job for daily run at 6 AM ET
gcloud scheduler jobs create http scout-daily-run \
    --location=${REGION} \
    --schedule="0 6 * * *" \
    --time-zone="America/New_York" \
    --uri="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/scout-daily-pipeline" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"trigger":"scheduled"}' \
    --attempt-deadline=600s \
    --max-retry-attempts=3

# Create health check job (every hour)
gcloud scheduler jobs create http scout-health-monitor \
    --location=${REGION} \
    --schedule="0 * * * *" \
    --uri="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/scout-health-check" \
    --http-method=GET \
    --attempt-deadline=30s

echo ""
echo "📊 Step 4: Creating BigQuery Datasets and Tables..."
echo "---------------------------------------------------"

# Create SCOUT dataset
bq mk --dataset \
    --location=US \
    --description="SCOUT Analytics and Anomaly Detection" \
    ${PROJECT_ID}:scout_analytics

# Create anomalies table
bq mk --table \
    ${PROJECT_ID}:scout_analytics.anomalies \
    schemas/anomalies_schema.json

# Create patterns table
bq mk --table \
    ${PROJECT_ID}:scout_analytics.patterns \
    schemas/patterns_schema.json

# Create predictions table
bq mk --table \
    ${PROJECT_ID}:scout_analytics.predictions \
    schemas/predictions_schema.json

echo ""
echo "🔐 Step 5: Setting up IAM Permissions..."
echo "----------------------------------------"

# Grant necessary permissions to service account
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectCreator"

echo ""
echo "🧪 Step 6: Running Test Invocation..."
echo "-------------------------------------"

# Test the function
FUNCTION_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/scout-health-check"
echo "Testing health check at: ${FUNCTION_URL}"
curl -X GET ${FUNCTION_URL}

echo ""
echo ""
echo "✅ SCOUT Deployment Complete!"
echo "============================="
echo ""
echo "📋 Deployment Summary:"
echo "  • Main Pipeline: https://${REGION}-${PROJECT_ID}.cloudfunctions.net/scout-daily-pipeline"
echo "  • Health Check: https://${REGION}-${PROJECT_ID}.cloudfunctions.net/scout-health-check"
echo "  • Schedule: Daily at 6:00 AM ET"
echo "  • Dataset: ${PROJECT_ID}.scout_analytics"
echo ""
echo "📊 Next Steps:"
echo "  1. Verify Cloud Scheduler jobs in Console"
echo "  2. Check function logs: gcloud functions logs read scout-daily-pipeline"
echo "  3. Monitor first run tomorrow at 6 AM ET"
echo "  4. Review alerts in storage bucket: gs://${PROJECT_ID}-scout-alerts"
echo ""
echo "🔍 Monitoring Commands:"
echo "  • View logs: gcloud functions logs read scout-daily-pipeline --limit=50"
echo "  • Check schedule: gcloud scheduler jobs list --location=${REGION}"
echo "  • Test run: gcloud scheduler jobs run scout-daily-run --location=${REGION}"
echo ""