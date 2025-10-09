// [R13] Cloud Storage configuration management (Direct public URLs)
// → provides: config-persistence-layer

// [R13] Property configuration interface
export interface PropertyConfig {
  property_id: string;
  dataset_id: string;
  client_name?: string | null;
  domain?: string | null;
  conversion_events?: string | null;
  notes?: string | null;
  is_configured: boolean;
}

// [R13] Cloud Storage response wrapper
interface CloudStorageResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// [R13] Cloud Storage public URLs
// → provides: cloud-storage-urls
const CLOUD_STORAGE_BASE = 'https://storage.googleapis.com';
const CONFIG_BUCKET = 'scout-config';
const RESULTS_BUCKET = 'scout-results';

// [R13] Load property configuration from Cloud Storage
// → provides: property-config-data
export async function loadPropertyConfig(): Promise<CloudStorageResponse<PropertyConfig[]>> {
  try {
    // Add cache-busting parameter to bypass CDN cache and ensure CORS headers are present
    const cacheBuster = `?t=${Date.now()}`;
    const response = await fetch(`${CLOUD_STORAGE_BASE}/${CONFIG_BUCKET}/properties.json${cacheBuster}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const properties = await response.json();

    // Handle both array format and object format with 'properties' key
    const data = Array.isArray(properties) ? properties : (properties.properties || []);

    return {
      success: true,
      data
    };
  } catch (error) {
    console.error('Failed to load configuration from Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// [R13] Save property configuration to Cloud Storage
// → needs: cloud-storage-write-api
// → provides: config-persistence
// NOTE: Direct writes to Cloud Storage require backend API or signed URLs
// For production, this should trigger a backend workflow or use Cloud Functions
export async function savePropertyConfig(_properties: PropertyConfig[]): Promise<CloudStorageResponse<void>> {
  try {
    // TODO: Implement Cloud Storage write via Cloud Function or signed URL
    // For MVP, this is read-only in production
    console.warn('Cloud Storage writes not implemented in production - configuration is read-only');

    return {
      success: false,
      error: 'Configuration updates require backend API (not available in production)'
    };
  } catch (error) {
    console.error('Failed to save configuration to Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// [R13] Load anomaly results from Cloud Storage
// → provides: anomaly-results-data
export async function loadAnomalyResults(): Promise<CloudStorageResponse<any>> {
  try {
    const response = await fetch(`${CLOUD_STORAGE_BASE}/${RESULTS_BUCKET}/scout_anomaly_results.json`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const results = await response.json();

    return {
      success: true,
      data: results
    };
  } catch (error) {
    console.error('Failed to load anomaly results from Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// [R14] Load segment-level anomaly results from Cloud Storage
// → provides: segment-anomaly-results-data
export async function loadSegmentAnomalyResults(): Promise<CloudStorageResponse<any>> {
  try {
    const response = await fetch(`${CLOUD_STORAGE_BASE}/${RESULTS_BUCKET}/scout_segment_anomalies.json`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const results = await response.json();

    return {
      success: true,
      data: results
    };
  } catch (error) {
    console.error('Failed to load segment anomaly results from Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}
