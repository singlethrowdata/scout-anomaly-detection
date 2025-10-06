# SCOUT Access Setup Instructions
*Statistical Client Observation & Unified Tracking*

## 🎯 What You Need
To implement Data Validation & Reconciliation [R4], SCOUT needs access to:
1. **STM BigQuery Project** (GA4 export data)
2. **GA4 Reporting API** (UI-accurate metrics)
3. **Client Property List** (50+ GA4 properties)

**✅ Service Account Provided**: `stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com`

## 📋 Step-by-Step Setup

### Step 1: BigQuery Project Access
```bash
# 1.1 Identify STM Analytics Project Name
# You need: The exact BigQuery project ID where GA4 exports are stored
# ✅ CONFIRMED: "st-ga4-data" (extracted from service account)

# 1.2 Verify GA4 Export Structure
# Run this query to confirm data structure:
bq query --use_legacy_sql=false \
"SELECT table_name, creation_time
FROM \`st-ga4-data\`.INFORMATION_SCHEMA.TABLES
WHERE table_name LIKE 'events_%'
LIMIT 5"

# 1.3 Grant SCOUT Service Account Access
# ✅ SERVICE ACCOUNT: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com
# You need: BigQuery Data Viewer + Job User roles
# Commands will be:
# gcloud projects add-iam-policy-binding st-ga4-data \
#   --member="serviceAccount:stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com" \
#   --role="roles/bigquery.dataViewer"
```

### Step 2: GA4 Reporting API Setup
```bash
# 2.1 Enable GA4 Reporting API
gcloud services enable analyticsreporting.googleapis.com
gcloud services enable analyticsdata.googleapis.com

# 2.2 Service Account Already Created ✅
# Using existing: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com

# 2.3 Service Account Key Management
# Key should already exist for: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com
# If needed: gcloud iam service-accounts keys create scout-credentials.json \
#   --iam-account=stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com
```

### Step 3: GA4 Property Access
```bash
# 3.1 Create Property List File
# You need to provide: List of GA4 Property IDs
# Create file: config/ga4_properties.json
# Format:
{
  "properties": [
    {
      "property_id": "123456789",
      "client_name": "client-1",
      "bigquery_dataset": "analytics_123456789"
    },
    {
      "property_id": "987654321",
      "client_name": "client-2",
      "bigquery_dataset": "analytics_987654321"
    }
  ]
}

# 3.2 Grant Service Account GA4 Access
# For each property, you need to:
# - Go to GA4 Admin > Account/Property > Property Access Management
# - Add stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com
# - Role: Viewer (minimum required)
```

### Step 4: Environment Configuration
```bash
# 4.1 Create Environment File
# Copy .env.template to .env and fill in:
cp .env.template .env

# 4.2 Required Environment Variables (✅ Pre-configured)
GOOGLE_CLOUD_PROJECT=st-ga4-data
BIGQUERY_PROJECT=st-ga4-data
GOOGLE_APPLICATION_CREDENTIALS=stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com
GA4_PROPERTIES_CONFIG=./config/ga4_properties.json

# 4.3 Install Dependencies
pip install -r requirements.txt
```

### Step 5: Test Access
```bash
# 5.1 Test BigQuery Connection
python scripts/test_schema_discovery.py --test-connection

# 5.2 Test GA4 API Connection
python scripts/scout_ga4_api_client.py --test-auth

# 5.3 Test Single Property
python scripts/test_data_validation.py --property-id 123456789 --days 1
```

## 🔧 What I Need From You

### Immediate (Required for next step):
1. **✅ BigQuery Project ID**: st-ga4-data (confirmed)
2. **✅ Service Account**: stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com (provided)
3. **Sample Property ID** - One GA4 property ID for initial testing
4. **Service Account Permission** - Can you grant BigQuery access to the service account?

### Soon (Within this week):
5. **Full Property List** - All 50+ GA4 property IDs and client names
6. **GA4 Admin Access** - To add service account to properties

### Example Commands You'll Run:
```bash
# Replace with actual property ID for testing
export PROPERTY_ID="123456789"

# Test if you have access to see the data
bq query --use_legacy_sql=false \
"SELECT COUNT(*) as total_tables
FROM \`st-ga4-data\`.INFORMATION_SCHEMA.TABLES
WHERE table_name LIKE 'events_%'"

# This should return a number > 0 if GA4 exports exist
```

## 🚨 Security Notes
- Service account stga4serviceaccount@st-ga4-data.iam.gserviceaccount.com should never be exposed
- Use Cloud IAM instead of key files in production
- Principle of least privilege - only grant minimum required permissions
- Rotate service account keys every 90 days

## 📞 Next Steps
1. **You provide**: Sample GA4 Property ID for testing
2. **I build**: Data validation framework with your access parameters
3. **We test**: Single property validation first
4. **Scale up**: Add all 50+ properties once working

Ready when you are! 🚀
