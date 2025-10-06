# [R9] SCOUT Email Digest Deployment Guide
# → provides: cloud-scheduler-deployment-instructions

## Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated
- Project ID: `stm-mvp`
- Region: `us-east1`

## Environment Variables (Required)

The Cloud Function needs these environment variables configured:

```bash
GMAIL_USER=submissions@singlethrow.com
GMAIL_APP_PASSWORD=<16-character app password>
SCOUT_EMAIL_RECIPIENTS=cblain@singlethrow.com,ccurtis@singlethrow.com
GOOGLE_APPLICATION_CREDENTIALS=<path to service account key> # Auto-configured in Cloud Functions
```

## Deployment Steps

### Step 1: Deploy Cloud Function

```bash
# Navigate to project root
cd c:/Users/Charles Blain/CascadeProjects/projects/PROJECT-058-AnomalyInsights

# Deploy the Cloud Function
gcloud functions deploy scout-email-digest \
  --gen2 \
  --runtime=python39 \
  --region=us-east1 \
  --source=deploy/cloud_function_email \
  --entry-point=send_daily_digest \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GMAIL_USER=submissions@singlethrow.com,SCOUT_EMAIL_RECIPIENTS=cblain@singlethrow.com,ccurtis@singlethrow.com \
  --set-secrets GMAIL_APP_PASSWORD=scout-gmail-password:latest \
  --timeout=540s \
  --memory=512MB
```

**Note**: Gmail App Password should be stored in Google Secret Manager as `scout-gmail-password`

### Step 2: Create Secret for Gmail App Password

```bash
# Create secret in Secret Manager
echo -n "<YOUR_16_CHAR_APP_PASSWORD>" | gcloud secrets create scout-gmail-password \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Function access to secret
gcloud secrets add-iam-policy-binding scout-gmail-password \
  --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 3: Create Cloud Scheduler Job

```bash
# Get the Cloud Function URL
FUNCTION_URL=$(gcloud functions describe scout-email-digest \
  --gen2 \
  --region=us-east1 \
  --format="value(serviceConfig.uri)")

# Create Cloud Scheduler job for 7 AM ET daily
gcloud scheduler jobs create http scout-daily-email-digest \
  --location=us-east1 \
  --schedule="0 7 * * *" \
  --time-zone="America/New_York" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --oidc-service-account-email="<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --description="Daily SCOUT email digest at 7 AM ET"
```

### Step 4: Test the Cloud Function

```bash
# Manual test trigger
gcloud scheduler jobs run scout-daily-email-digest --location=us-east1

# View logs
gcloud functions logs read scout-email-digest --gen2 --region=us-east1 --limit=50
```

## Verification

After deployment, verify:

1. **Cloud Function deployed**: Check Cloud Console → Cloud Functions
2. **Secret accessible**: Cloud Function has `secretmanager.secretAccessor` role
3. **Scheduler created**: Check Cloud Console → Cloud Scheduler
4. **First run successful**: Check function logs after 7 AM ET next day

## Monitoring

```bash
# View Cloud Scheduler job status
gcloud scheduler jobs describe scout-daily-email-digest --location=us-east1

# View Cloud Function logs
gcloud functions logs read scout-email-digest --gen2 --region=us-east1 --limit=100

# Pause scheduler (if needed)
gcloud scheduler jobs pause scout-daily-email-digest --location=us-east1

# Resume scheduler
gcloud scheduler jobs resume scout-daily-email-digest --location=us-east1
```

## Costs

**Estimated Monthly Costs**:
- Cloud Function: ~$0.40 (30 invocations/month @ 10s runtime)
- Cloud Scheduler: $0.10 (1 job)
- **Total**: ~$0.50/month

## Troubleshooting

### Issue: Cloud Function times out
**Solution**: Increase timeout with `--timeout=540s` (9 minutes max for Gen2)

### Issue: Gmail authentication fails
**Solution**: Verify Gmail App Password in Secret Manager and IAM permissions

### Issue: Scheduler not triggering
**Solution**: Check timezone is `America/New_York` and cron expression `0 7 * * *`

### Issue: Email not received
**Solution**:
1. Check Cloud Function logs for delivery status
2. Verify `SCOUT_EMAIL_RECIPIENTS` environment variable
3. Check Gmail sent folder for submissions@singlethrow.com

## Production Deployment Checklist

- [ ] Gmail App Password stored in Secret Manager
- [ ] Cloud Function deployed successfully
- [ ] Environment variables configured correctly
- [ ] Cloud Scheduler job created with 7 AM ET schedule
- [ ] Manual test run successful
- [ ] First automated email received at 7 AM ET
- [ ] Logs monitored for 7 days to confirm reliability
- [ ] STATE.md updated with production status

---

**Deployment prepared**: 2025-10-03
**Next review**: After first 7 AM ET automated run
