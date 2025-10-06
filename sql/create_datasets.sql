-- SCOUT BigQuery Dataset Creation
-- Creates foundation datasets for automated GA4 anomaly detection
-- Cost Estimate: <$1 (dataset creation only, no data processing)

-- Main SCOUT metadata dataset
CREATE SCHEMA IF NOT EXISTS `stm-analytics-project.scout_metadata`
OPTIONS(
  description="SCOUT metadata storage - client schemas, configurations, and discovery results",
  location="US"
);

-- SCOUT processed results dataset  
CREATE SCHEMA IF NOT EXISTS `stm-analytics-project.scout_results`
OPTIONS(
  description="SCOUT processing outputs - anomalies, patterns, and alerts",
  location="US"
);

-- SCOUT ML models dataset
CREATE SCHEMA IF NOT EXISTS `stm-analytics-project.scout_ml`
OPTIONS(
  description="SCOUT machine learning models and training data",
  location="US"
);

-- Schema registry table for dynamic client property discovery [R1]
CREATE OR REPLACE TABLE `stm-analytics-project.scout_metadata.client_schemas` (
  client_id STRING NOT NULL,
  property_id STRING NOT NULL,
  dataset_name STRING NOT NULL,
  table_name STRING NOT NULL,
  schema_json STRING NOT NULL,  -- Full table schema as JSON
  custom_events ARRAY<STRING>,  -- List of custom event names discovered
  conversion_events ARRAY<STRING>, -- Conversion events identified
  last_discovered TIMESTAMP NOT NULL,
  schema_hash STRING NOT NULL,  -- Hash to detect schema changes
  is_active BOOLEAN DEFAULT TRUE,
  discovered_by STRING DEFAULT 'scout_schema_discovery'
)
PARTITION BY DATE(last_discovered)
CLUSTER BY client_id, property_id
OPTIONS(
  description="Registry of all discovered GA4 schemas and custom events per client"
);

-- Discovery run tracking for monitoring [R1]
CREATE OR REPLACE TABLE `stm-analytics-project.scout_metadata.discovery_runs` (
  run_id STRING NOT NULL,
  run_timestamp TIMESTAMP NOT NULL,
  clients_processed INT64,
  schemas_discovered INT64,
  errors_encountered INT64,
  processing_duration_seconds FLOAT64,
  status STRING NOT NULL, -- 'success', 'partial', 'failed'
  error_details STRING,
  next_run_scheduled TIMESTAMP
)
PARTITION BY DATE(run_timestamp)
ORDER BY run_timestamp DESC
OPTIONS(
  description="Tracking table for SCOUT schema discovery execution monitoring"
);