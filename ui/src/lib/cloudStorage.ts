// [R13] Cloud Storage configuration management (Proxy-based)
// → needs: proxy-server-api
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

// [R13] Proxy server configuration
// → provides: proxy-api-url
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

// [R13] Load property configuration from Cloud Storage via proxy
// → needs: proxy-api-url
// → provides: property-config-data
export async function loadPropertyConfig(): Promise<CloudStorageResponse<PropertyConfig[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config/properties`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    const config = await response.json();

    return {
      success: true,
      data: config.properties || []
    };
  } catch (error) {
    console.error('Failed to load configuration from Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// [R13] Save property configuration to Cloud Storage via proxy
// → needs: proxy-api-url, property-config-data
// → provides: config-persistence
export async function savePropertyConfig(properties: PropertyConfig[]): Promise<CloudStorageResponse<void>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/config/properties`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ properties })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return { success: true };
  } catch (error) {
    console.error('Failed to save configuration to Cloud Storage:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// [R13] Load anomaly results from Cloud Storage via proxy
// → needs: proxy-api-url
// → provides: anomaly-results-data
export async function loadAnomalyResults(): Promise<CloudStorageResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/results/anomalies`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP ${response.status}`);
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

// [R14] Load segment-level anomaly results from Cloud Storage via proxy
// → needs: proxy-api-url
// → provides: segment-anomaly-results-data
export async function loadSegmentAnomalyResults(): Promise<CloudStorageResponse<any>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/results/segment-anomalies`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP ${response.status}`);
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
