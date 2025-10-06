# 🔍 SCOUT - QUICK START GUIDE
*Statistical Client Observation & Unified Tracking*

## Meta-Context: SCOUT is Ready for Deployment
**What exists**: Complete project structure with SCOUT branding, WBS plan, starter Python scripts
**What doesn't**: BigQuery access, actual client data mappings, deployed functions
**Confidence**: 85% you can have SCOUT operational in 2 days

---

## STEP 1: Environment Setup for SCOUT (30 minutes)
**Assumption**: You have Python 3.10+ installed

```bash
# Navigate to SCOUT headquarters
cd "C:\Users\Charles Blain\CascadeProjects\projects\PROJECT-058-AnomalyInsights"

# Create SCOUT's virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install SCOUT dependencies
pip install -r requirements.txt
```

**Common failure**: pip fails on google-cloud packages
**Solution**: Update pip first: `python -m pip install --upgrade pip`
**Confidence**: 90% this works first try

---

## STEP 2: BigQuery Authentication for SCOUT

### Option A: Service Account (Recommended for Production)
**Confidence**: 95% this is the right approach

1. Go to GCP Console > IAM & Admin > Service Accounts
2. Create service account: `anomaly-detector@stm-analytics.iam`
3. Grant roles:
   - BigQuery Data Editor
   - BigQuery Job User
4. Create key (JSON format)
5. Save to project root as `service-account.json`
6. Update .env file

### Option B: Local Auth (Faster for Testing)
**Confidence**: Good for development, not production

```bash
gcloud auth application-default login
gcloud config set project stm-analytics-YOURPROJECT
```

**Risk**: This uses YOUR personal credentials
**Mitigation**: Fine for testing, switch to service account before deploying

---

## STEP 3: Configure Your Clients (The Hard Truth)

**Reality check**: You need to map client names to BigQuery datasets

1. Copy `.env.template` to `.env`
2. Open `scripts/schema_discovery.py`
3. Find the `CLIENT_DATASET_MAP` dictionary
4. Replace with your ACTUAL client mappings:

```python
CLIENT_DATASET_MAP = {
    'acme_corp': 'analytics_123456789',    # Real GA4 property ID
    'beta_inc': 'analytics_987654321',     # Another real one
    # Add all 50 clients here
}
```

**Meta-question**: How are your GA4 datasets actually named?
- Standard pattern?: `analytics_[property_id]`
- Custom names?: Need manual mapping
- **CRITICAL**: Get this list from whoever set up BigQuery exports

---

## STEP 4: Test SCOUT's Reconnaissance (Moment of Truth)

```bash
# Launch SCOUT's first mission
python scripts/scout_schema_discovery.py
```

**Expected SCOUT report**:
```
🔍 SCOUT SCHEMA DISCOVERY MISSION
Statistical Client Observation & Unified Tracking
==================================================

Setting up SCOUT metadata tables...
Created dataset stm_analytics_metadata
SCOUT beginning schema reconnaissance...
--- Processing acme_corp ---
✓ Discovered 47 event types
  - Custom events: 23
  - Conversion events: 5
  - Unique parameters: 89

SCOUT MISSION COMPLETE
```

**Common failures and fixes**:

1. **"Permission denied"**
   - Check service account has BigQuery Data Viewer on client datasets
   - Confidence: 60% this happens on first run

2. **"Dataset not found"**
   - Your dataset names are wrong in CLIENT_DATASET_MAP
   - Run this to list all datasets:
   ```python
   from google.cloud import bigquery
   client = bigquery.Client()
   for dataset in client.list_datasets():
       print(dataset.dataset_id)
   ```

3. **"Table events_* not found"**
   - GA4 export not enabled for this property
   - Takes 24 hours after enabling to get data
   - **Alternative perspective**: Maybe tables are named differently?

---

## STEP 5: Verify Results in BigQuery

```sql
-- Run this in BigQuery console
SELECT 
    client_id,
    discovered_at,
    event_count,
    JSON_EXTRACT_ARRAY(custom_events) as events
FROM `stm-analytics.stm_analytics_metadata.client_schemas`
ORDER BY discovered_at DESC
```

**What you're looking for**:
- ✅ All clients have entries
- ✅ Custom events look correct
- ✅ Conversion events identified
- ❌ If empty, check Step 4 failures

---

## STEP 6: Next Implementation Phase

### What to build next (in order):

1. **Anomaly Detection Query** (4 hours)
   ```python
   # Create scripts/detect_anomalies.py
   # Implement z-score detection on session counts
   # Test with one metric first
   ```

2. **Cloud Function Wrapper** (2 hours)
   ```python
   # Create functions/daily_detection/main.py
   # Wrap detection script for Cloud Functions
   # Deploy with: gcloud functions deploy
   ```

3. **Email Report** (3 hours)
   ```python
   # Create scripts/send_alerts.py
   # Use SendGrid templates
   # Test with your email first
   ```

---

## 🔴 CRITICAL DECISIONS NEEDED FROM YOU

1. **Client Dataset Naming Pattern?**
   - Need exact BigQuery dataset names
   - Alternative: Query INFORMATION_SCHEMA.SCHEMATA

2. **Which 3 Clients for Pilot?**
   - Pick diverse: Big, Medium, Small traffic
   - Different industries if possible
   - **Why**: Tests edge cases early

3. **Email Report Timing?**
   - 7 AM ET currently planned
   - Adjust for your team's schedule?

4. **Teams Channel Setup?**
   - Who creates webhooks?
   - Different channels per severity?

---

## 📊 Success Metrics for SCOUT This Week

**By Friday, SCOUT should have**:
- ✅ All 50 client schemas discovered via SCOUT reconnaissance
- ✅ Basic SCOUT anomaly detection running locally
- ✅ One test SCOUT alert email sent with real anomalies
- ✅ SCOUT Cloud Function deployed (even if manual trigger)

**Confidence**: 70% achievable if BigQuery access works
**Main risk**: Unknown client data structures
**Mitigation**: Start SCOUT with 3 clients, scale after success

---

## 🤔 Meta-Analysis: Alternative SCOUT Approaches

**What if BigQuery access is harder than expected?**
- Plan B: Start SCOUT with GA4 API for 3 clients
- Pro: Faster SCOUT deployment
- Con: SCOUT won't scale to 50 clients
- Decision point: If BigQuery blocked for >2 days, pivot SCOUT

**What if custom events are too varied for SCOUT?**
- Plan B: SCOUT focuses only on traffic metrics initially
- Pro: Consistent across all SCOUT territories
- Con: Less valuable SCOUT intelligence
- Decision point: If >50% clients have unique schemas

**What if email isn't the right SCOUT delivery method?**
- Plan B: SCOUT Slack integration instead
- Pro: Better for instant SCOUT alerts
- Con: Another integration for SCOUT to manage
- Decision point: Ask AMs their SCOUT preference

---

## 💬 Let's Collaborate on SCOUT

**I'm making these assumptions about SCOUT** (tell me if wrong):
1. All GA4 data is in `analytics_*` datasets for SCOUT to patrol
2. You have BigQuery Admin access for SCOUT
3. Python environment is comfortable for SCOUT development
4. Email is primary SCOUT alert channel
5. 50 clients is SCOUT's actual territory

**Questions for SCOUT deployment**:
1. What's the ACTUAL project ID for SCOUT in GCP?
2. Do you have client->dataset mappings for SCOUT?
3. Any clients with weird GA4 setups SCOUT should know about?
4. Preferred Python IDE for SCOUT development? (VS Code setup available)

**Your next action**: 
Try SCOUT Steps 1-4 and let me know where SCOUT hits the first obstacle.

---

*Remember: SCOUT is built for value, not perfection. Get SCOUT detecting anomalies for 3 clients, then scale SCOUT's territory.*