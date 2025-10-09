// [R18]: Spam Detection Dashboard - P1 Bot Traffic Detection
// → needs: spam-alerts from Cloud Storage
// → provides: spam-monitoring, quality-signals-ui
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { Shield, RefreshCw, Download, TrendingUp, Filter } from 'lucide-react';

// [R18]: Spam alert data structure
interface SpamAlert {
  property_id: string;
  property_name: string;
  alert_type: string;
  severity: 'warning' | 'critical';
  metric: string;
  current_value: number;
  baseline_value: number;
  z_score: number;
  traffic_source: string;
  message: string;
  detected_at: string;
}

interface SpamResults {
  detector: string;
  timestamp: string;
  alerts: SpamAlert[];
  summary: {
    total_properties_analyzed: number;
    total_alerts: number;
    warning_alerts: number;
  };
}

export default function Spam() {
  const [results, setResults] = useState<SpamResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<string>('all');
  const [selectedDimension, setSelectedDimension] = useState<string>('all');

  // [R18]: Load spam alerts from Cloud Storage via proxy
  const loadResults = async () => {
    setLoading(true);
    setError(null);
    try {
      // Add cache-busting to bypass CDN cache
      const response = await fetch(`https://storage.googleapis.com/scout-results/scout_spam_alerts.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error('Failed to load spam alerts');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load spam alerts');
      console.error('Error loading spam alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  const filteredAlerts = results?.alerts.filter(alert => {
    if (selectedProperty !== 'all' && alert.property_id !== selectedProperty) return false;
    if (selectedDimension !== 'all' && alert.traffic_source !== selectedDimension) return false;
    return true;
  }) || [];

  const uniqueProperties = [...new Set(results?.alerts.map(a => a.property_id) || [])];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-scout-yellow mx-auto mb-4" />
          <p className="text-scout-gray">Loading spam detection results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md border-scout-yellow">
          <CardHeader>
            <CardTitle className="text-scout-yellow">Error Loading Spam Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-scout-gray mb-4">{error}</p>
            <Button onClick={loadResults} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Gradient Header Section */}
      <div className="bg-gradient-to-r from-scout-blue to-scout-blue/90 rounded-lg shadow-lg border-4 border-scout-yellow p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <Shield className="w-12 h-12 text-scout-yellow" />
          <div>
            <h2 className="text-3xl font-bold">🛡️ Spam Detection</h2>
            <p className="text-blue-100">P1 Bot Traffic Identification - Quality Signal Analysis</p>
          </div>
        </div>
        <p className="text-blue-50 max-w-3xl">
          Identifies bot traffic and spam sessions through Z-score analysis combined with quality signals (bounce rate, session duration). Protects data integrity across geography and traffic source dimensions.
        </p>
      </div>

      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-scout-gray">
            {results && results.timestamp && `Last scanned: ${new Date(results.timestamp).toLocaleString()}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadResults} variant="outline" className="border-scout-blue text-scout-blue hover:bg-scout-blue hover:text-white">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" className="border-scout-gray text-scout-gray hover:bg-scout-gray hover:text-white">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-scout-blue bg-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Properties Monitored</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-scout-blue">{results?.summary?.total_properties_analyzed || uniqueProperties.length || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-yellow bg-yellow-100">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Spam Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-yellow">{results?.summary?.total_alerts || results?.alerts?.length || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-green bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Quality Check</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-scout-gray font-semibold">
              Bounce Rate Analysis
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="border-scout-blue">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-scout-blue">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-medium mb-2 block text-scout-blue">Property</label>
              <select
                value={selectedProperty}
                onChange={(e) => setSelectedProperty(e.target.value)}
                className="w-full px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
              >
                <option value="all">All Properties</option>
                {uniqueProperties.map(propId => (
                  <option key={propId} value={propId}>
                    {results?.alerts.find(a => a.property_id === propId)?.property_name || propId}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block text-scout-blue">Dimension</label>
              <select
                value={selectedDimension}
                onChange={(e) => setSelectedDimension(e.target.value)}
                className="w-full px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
              >
                <option value="all">All Traffic Sources</option>
                <option value="organic">Organic</option>
                <option value="paid">Paid</option>
                <option value="direct">Direct</option>
                <option value="referral">Referral</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedProperty('all');
                setSelectedDimension('all');
              }}
              className="border-scout-gray text-scout-gray hover:bg-scout-gray hover:text-white"
            >
              Clear Filters
            </Button>
            <span className="ml-3 text-sm text-scout-gray">
              Showing {filteredAlerts.length} of {results?.alerts.length || 0} spam alerts
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Spam alerts */}
      <Card className="border-scout-yellow">
        <CardHeader>
          <CardTitle className="text-scout-blue">Spam Traffic Detection</CardTitle>
          <CardDescription className="text-scout-gray">
            Bot traffic identified through Z-score analysis and quality signals
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-br from-scout-green/10 to-green-100 rounded-lg border-2 border-scout-green">
                <div className="text-6xl mb-4">✅</div>
                <p className="text-xl font-semibold text-scout-green">No Spam Detected</p>
                <p className="text-sm text-scout-gray mt-2">All traffic appears legitimate</p>
              </div>
            ) : (
              filteredAlerts.map((alert, index) => (
                <div
                  key={`${alert.property_id}-${alert.detected_at}-${index}`}
                  className="p-5 border-l-4 border-scout-yellow bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Shield className="h-5 w-5 text-scout-yellow" />
                        <h3 className="font-bold text-scout-blue">{alert.property_name || alert.property_id}</h3>
                        <span className="px-2 py-1 bg-scout-yellow text-white text-xs font-semibold rounded">
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 bg-scout-blue/10 text-scout-blue text-xs rounded border border-scout-blue">
                          Traffic: {alert.traffic_source}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm mt-3">
                        <div>
                          <p className="text-scout-gray">Bounce Rate (Spike)</p>
                          <p className="font-semibold text-scout-yellow flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" />
                            {alert.current_value.toFixed(1)}% (+{alert.z_score.toFixed(1)}σ)
                          </p>
                        </div>
                        <div>
                          <p className="text-scout-gray">Detected</p>
                          <p className="font-semibold text-scout-blue">{new Date(alert.detected_at).toLocaleDateString()}</p>
                        </div>
                        <div className="bg-scout-blue/10 p-2 rounded border border-scout-blue">
                          <p className="text-scout-gray text-xs">Current Value</p>
                          <p className="font-bold text-scout-red">{alert.current_value.toFixed(1)}%</p>
                        </div>
                        <div className="bg-scout-green/10 p-2 rounded border border-scout-green">
                          <p className="text-scout-gray text-xs">Baseline</p>
                          <p className="font-bold text-scout-green">{alert.baseline_value.toFixed(1)}%</p>
                        </div>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="border-scout-blue text-scout-blue hover:bg-scout-blue hover:text-white">
                      Investigate
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
