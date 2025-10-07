// [R17]: Disaster Detection Dashboard - P0 Critical Failures
// → needs: disaster-alerts from Cloud Storage
// → provides: disaster-monitoring, critical-alerts-ui
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { AlertTriangle, RefreshCw, Download, TrendingDown } from 'lucide-react';

// [R17]: Disaster alert data structure
interface DisasterAlert {
  property_id: string;
  domain: string;
  date: string;
  disaster_type: 'zero_sessions' | 'zero_conversions' | 'traffic_drop';
  current_value: number;
  baseline_value: number;
  drop_percentage: number;
  severity: 'critical';
}

interface DisasterResults {
  generated_at: string;
  properties_analyzed: number;
  total_disasters: number;
  alerts: DisasterAlert[];
}

export default function Disasters() {
  const [results, setResults] = useState<DisasterResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<string>('all');

  // [R17]: Load disaster alerts from Cloud Storage via proxy
  const loadResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('https://storage.googleapis.com/scout-results/scout_disaster_alerts.json');
      if (!response.ok) {
        throw new Error('Failed to load disaster alerts');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load disaster alerts');
      console.error('Error loading disasters:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  const filteredAlerts = results?.alerts.filter(alert => {
    if (selectedProperty !== 'all' && alert.property_id !== selectedProperty) return false;
    return true;
  }) || [];

  const uniqueProperties = [...new Set(results?.alerts.map(a => a.property_id) || [])];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-scout-red mx-auto mb-4" />
          <p className="text-scout-gray">Loading disaster alerts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md border-scout-red">
          <CardHeader>
            <CardTitle className="text-scout-red">Error Loading Disasters</CardTitle>
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
      <div className="bg-gradient-to-r from-scout-blue to-scout-blue/90 rounded-lg shadow-lg border-4 border-scout-red p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <AlertTriangle className="w-12 h-12 text-scout-red" />
          <div>
            <h2 className="text-3xl font-bold">🚨 Disaster Detection</h2>
            <p className="text-blue-100">P0 Critical Failures - Immediate Action Required</p>
          </div>
        </div>
        <p className="text-blue-50 max-w-3xl">
          Site-wide catastrophic failures requiring immediate intervention. Detects zero sessions, zero conversions, and 90%+ traffic drops before clients notice.
        </p>
      </div>

      {/* Critical banner */}
      {filteredAlerts.length > 0 && (
        <div className="bg-gradient-to-r from-scout-red to-red-700 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center gap-4">
            <AlertTriangle className="h-10 w-10" />
            <div>
              <h2 className="text-2xl font-bold">⚠️ ACT NOW - CRITICAL FAILURES DETECTED</h2>
              <p className="text-red-100">
                {filteredAlerts.length} site-wide {filteredAlerts.length === 1 ? 'disaster' : 'disasters'} requiring immediate attention
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-scout-gray">
            {results && `Last scanned: ${new Date(results.generated_at).toLocaleString()}`}
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
            <div className="text-2xl font-bold text-scout-blue">{results?.properties_analyzed || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-red bg-red-100">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-red">Critical Disasters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-red">{results?.total_disasters || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-green">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${filteredAlerts.length === 0 ? 'text-scout-green' : 'text-scout-red'}`}>
              {filteredAlerts.length === 0 ? '✅ All Clear' : '⚠️ Action Required'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      {uniqueProperties.length > 1 && (
        <Card className="border-scout-blue">
          <CardHeader>
            <CardTitle className="text-sm text-scout-blue">Filter by Property</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              value={selectedProperty}
              onChange={(e) => setSelectedProperty(e.target.value)}
              className="w-full max-w-xs px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
            >
              <option value="all">All Properties</option>
              {uniqueProperties.map(propId => (
                <option key={propId} value={propId}>
                  {results?.alerts.find(a => a.property_id === propId)?.domain || propId}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {/* Disaster alerts */}
      <Card className="border-scout-red">
        <CardHeader>
          <CardTitle className="text-scout-blue">Active Disaster Alerts</CardTitle>
          <CardDescription className="text-scout-gray">
            Site-wide failures requiring immediate intervention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-br from-scout-green/10 to-green-100 rounded-lg border-2 border-scout-green">
                <div className="text-6xl mb-4">✅</div>
                <p className="text-xl font-semibold text-scout-green">No Disasters Detected</p>
                <p className="text-sm text-scout-gray mt-2">All properties are operating normally</p>
              </div>
            ) : (
              filteredAlerts.map((alert, index) => (
                <div
                  key={`${alert.property_id}-${alert.date}-${index}`}
                  className="p-6 border-2 border-scout-red rounded-lg bg-red-50 hover:bg-red-100 transition-colors shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <AlertTriangle className="h-6 w-6 text-scout-red" />
                        <h3 className="text-xl font-bold text-scout-blue">{alert.domain}</h3>
                        <span className="px-3 py-1 bg-scout-red text-white text-xs font-bold rounded-full">
                          P0 CRITICAL
                        </span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <p className="text-scout-gray">
                          <span className="font-semibold text-scout-blue">Disaster Type:</span>{' '}
                          {alert.disaster_type.replace(/_/g, ' ').toUpperCase()}
                        </p>
                        <p className="text-scout-gray">
                          <span className="font-semibold text-scout-blue">Date:</span>{' '}
                          {new Date(alert.date).toLocaleDateString()}
                        </p>
                        <div className="flex items-center gap-2 text-scout-red font-semibold">
                          <TrendingDown className="h-5 w-5" />
                          <span className="text-lg">
                            {alert.drop_percentage.toFixed(0)}% DROP
                          </span>
                        </div>
                        <p className="text-scout-gray">
                          Current: <span className="font-mono font-semibold text-scout-red">{alert.current_value}</span>
                          {' '} | Baseline: <span className="font-mono text-scout-gray">{alert.baseline_value}</span>
                        </p>
                      </div>
                    </div>
                    <Button className="bg-scout-red hover:bg-red-700 text-white">
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
