// [R13] Cloud Storage Proxy Server (Node.js)
// → needs: @google-cloud/storage, express, cors
// → provides: gcs-proxy-api

const express = require('express');
const cors = require('cors');
const { Storage } = require('@google-cloud/storage');

const app = express();
const port = process.env.PORT || 5000;

// [R13] Initialize Storage client with Application Default Credentials
// → provides: gcs-client
const storage = new Storage({
  projectId: process.env.GCP_PROJECT_ID || 'st-ga4-data',
});

const CONFIG_BUCKET = process.env.GCS_CONFIG_BUCKET || 'scout-config';
const RESULTS_BUCKET = process.env.GCS_RESULTS_BUCKET || 'scout-results';

// [R13] Enable CORS for local development
app.use(cors());
app.use(express.json());

// [R13] Health check endpoint
// → provides: server-health
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// [R13] Load property configuration from Cloud Storage
// → needs: gcs-client
// → provides: config-read-api
app.get('/api/config/properties', async (req, res) => {
  try {
    const bucket = storage.bucket(CONFIG_BUCKET);
    const file = bucket.file('properties.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ properties: [] });
    }

    const [contents] = await file.download();
    const config = JSON.parse(contents.toString('utf-8'));

    res.json(config);
  } catch (error) {
    console.error('Error loading configuration:', error);
    res.status(500).json({
      error: 'Failed to load configuration',
      message: error.message
    });
  }
});

// [R13] Save property configuration to Cloud Storage
// → needs: gcs-client
// → provides: config-write-api
app.post('/api/config/properties', async (req, res) => {
  try {
    const { properties } = req.body;

    if (!properties || !Array.isArray(properties)) {
      return res.status(400).json({
        error: 'Invalid request body. Expected { properties: [...] }'
      });
    }

    const bucket = storage.bucket(CONFIG_BUCKET);
    const file = bucket.file('properties.json');

    const config = {
      properties,
      updated: new Date().toISOString(),
      updatedBy: 'scout-ui',
      version: '1.0'
    };

    await file.save(JSON.stringify(config, null, 2), {
      contentType: 'application/json',
      metadata: {
        updated: config.updated,
        updatedBy: config.updatedBy
      }
    });

    res.json({ success: true, updated: config.updated });
  } catch (error) {
    console.error('Error saving configuration:', error);
    res.status(500).json({
      error: 'Failed to save configuration',
      message: error.message
    });
  }
});

// [R13] Load anomaly results from Cloud Storage
// → needs: gcs-client
// → provides: results-read-api
app.get('/api/results/anomalies', async (req, res) => {
  try {
    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('anomalies.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ anomalies: [], generated: null });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading anomaly results:', error);
    res.status(500).json({
      error: 'Failed to load anomaly results',
      message: error.message
    });
  }
});

// [R14] Load segment-level anomaly results from Cloud Storage
// → needs: gcs-client
// → provides: segment-anomalies-read-api
app.get('/api/results/segment-anomalies', async (req, res) => {
  try {
    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('segment_anomalies.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ anomalies: [], generated: null });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading segment anomaly results:', error);
    res.status(500).json({
      error: 'Failed to load segment anomaly results',
      message: error.message
    });
  }
});

// [R17] Load disaster alerts from Cloud Storage
// → needs: gcs-client
// → provides: disaster-alerts-read-api
app.get('/api/results/disasters', async (req, res) => {
  try {
    console.log(`[DISASTERS] Received request at ${new Date().toISOString()}`);
    console.log(`[DISASTERS] Bucket: ${RESULTS_BUCKET}`);

    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('disaster_alerts.json');

    console.log(`[DISASTERS] Checking file existence: disaster_alerts.json`);
    const [exists] = await file.exists();
    console.log(`[DISASTERS] File exists: ${exists}`);

    if (!exists) {
      console.log(`[DISASTERS] File not found, returning empty result`);
      return res.status(404).json({
        error: 'File not found in Cloud Storage',
        bucket: RESULTS_BUCKET,
        file: 'disaster_alerts.json'
      });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading disaster alerts:', error);
    res.status(500).json({
      error: 'Failed to load disaster alerts',
      message: error.message
    });
  }
});

// [R18] Load spam alerts from Cloud Storage
// → needs: gcs-client
// → provides: spam-alerts-read-api
app.get('/api/results/spam', async (req, res) => {
  try {
    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('spam_alerts.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ alerts: [], generated_at: null, properties_analyzed: 0, total_spam_alerts: 0 });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading spam alerts:', error);
    res.status(500).json({
      error: 'Failed to load spam alerts',
      message: error.message
    });
  }
});

// [R19] Load record alerts from Cloud Storage
// → needs: gcs-client
// → provides: record-alerts-read-api
app.get('/api/results/records', async (req, res) => {
  try {
    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('record_alerts.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ alerts: [], generated_at: null, properties_analyzed: 0, total_records: 0, highs: 0, lows: 0 });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading record alerts:', error);
    res.status(500).json({
      error: 'Failed to load record alerts',
      message: error.message
    });
  }
});

// [R20] Load trend alerts from Cloud Storage
// → needs: gcs-client
// → provides: trend-alerts-read-api
app.get('/api/results/trends', async (req, res) => {
  try {
    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('trend_alerts.json');

    const [exists] = await file.exists();
    if (!exists) {
      return res.json({ alerts: [], generated_at: null, properties_analyzed: 0, total_trends: 0, upward_trends: 0, downward_trends: 0 });
    }

    const [contents] = await file.download();
    const results = JSON.parse(contents.toString('utf-8'));

    res.json(results);
  } catch (error) {
    console.error('Error loading trend alerts:', error);
    res.status(500).json({
      error: 'Failed to load trend alerts',
      message: error.message
    });
  }
});

// [R9] Save anomaly results to Cloud Storage
// → needs: gcs-client
// → provides: results-write-api
app.post('/api/results/anomalies', async (req, res) => {
  try {
    const anomalyData = req.body;

    if (!anomalyData || !anomalyData.anomalies) {
      return res.status(400).json({
        error: 'Invalid request body. Expected anomaly results object with anomalies array'
      });
    }

    const bucket = storage.bucket(RESULTS_BUCKET);
    const file = bucket.file('anomalies.json');

    await file.save(JSON.stringify(anomalyData, null, 2), {
      contentType: 'application/json',
      metadata: {
        generated: anomalyData.generated_at || new Date().toISOString(),
        uploadedBy: 'scout-test-script'
      }
    });

    res.json({
      success: true,
      uploaded: anomalyData.generated_at,
      anomalies_count: anomalyData.anomalies.length
    });
  } catch (error) {
    console.error('Error saving anomaly results:', error);
    res.status(500).json({
      error: 'Failed to save anomaly results',
      message: error.message
    });
  }
});

// [R13] Start server
app.listen(port, () => {
  console.log(`✅ SCOUT Cloud Storage Proxy running on http://localhost:${port}`);
  console.log(`📦 Project: ${process.env.GCP_PROJECT_ID || 'st-ga4-data'}`);
  console.log(`🪣 Config Bucket: ${CONFIG_BUCKET}`);
  console.log(`🪣 Results Bucket: ${RESULTS_BUCKET}`);
});
