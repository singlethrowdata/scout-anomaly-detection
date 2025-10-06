// [R19]: Record Detection Dashboard - P1-P3 Historical Highs/Lows
// → needs: record-alerts from Cloud Storage
// → provides: record-monitoring, 90day-comparison-ui
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { Trophy, TrendingDown, RefreshCw, Download, Filter } from 'lucide-react';

// [R19]: Record alert data structure (matches detector output)
interface RecordAlert {
  property_id: string;
  domain: string;
  date: string;
  anomaly_type: string;
  priority: string;
  record_type: 'high' | 'low';
  dimension: 'overall' | 'device' | 'traffic_source' | 'landing_page';
  dimension_value: string;
  metric: string;
  value: number;
  previous_record: number;
  decline?: number;
  increase?: number;
  message: string;
  action_required: string;
  business_impact: number;
  detected_at: string;
}

interface RecordResults {
  generated_at: string;
  detector_type: string;
  priority: string;
  properties_analyzed: number;
  total_alerts: number;
  dimensions: string[];
  alerts: RecordAlert[];
}

export default function Records() {
  const [results, setResults] = useState<RecordResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<string>('all');
  const [selectedRecordType, setSelectedRecordType] = useState<string>('all');
  const [selectedDimension, setSelectedDimension] = useState<string>('all');

  // [R19]: Load record alerts from Cloud Storage via proxy
  const loadResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:5000/api/results/records');
      if (!response.ok) {
        throw new Error('Failed to load record alerts');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load record alerts');
      console.error('Error loading records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  const filteredAlerts = results?.alerts.filter(alert => {
    if (selectedProperty !== 'all' && alert.property_id !== selectedProperty) return false;
    if (selectedRecordType !== 'all' && alert.record_type !== selectedRecordType) return false;
    if (selectedDimension !== 'all' && alert.dimension !== selectedDimension) return false;
    return true;
  }) || [];

  const uniqueProperties = [...new Set(results?.alerts.map(a => a.property_id) || [])];

  // [R19]: Calculate record highs and lows from alerts
  const recordHighs = results?.alerts.filter(a => a.record_type === 'high').length || 0;
  const recordLows = results?.alerts.filter(a => a.record_type === 'low').length || 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-scout-blue mx-auto mb-4" />
          <p className="text-scout-gray">Loading record detection results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md border-scout-blue">
          <CardHeader>
            <CardTitle className="text-scout-blue">Error Loading Records</CardTitle>
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
      <div className="bg-gradient-to-r from-scout-blue to-scout-blue/90 rounded-lg shadow-lg border border-scout-blue/20 p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <Trophy className="w-12 h-12 text-white" />
          <div>
            <h2 className="text-3xl font-bold">🏆 Record Detection</h2>
            <p className="text-blue-100">P1-P3 Historical Highs & Lows - 90-Day Context</p>
          </div>
        </div>
        <p className="text-blue-50 max-w-3xl">
          Tracks all-time record highs and lows across devices, traffic sources, and landing pages within the past 90 days. Identifies breakthrough performance and concerning declines for strategic insights.
        </p>
      </div>

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
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-scout-blue bg-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Properties Monitored</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-scout-blue">{results?.properties_analyzed || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-green bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Record Highs 🏆</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-green">{recordHighs}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-red bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Record Lows ⚠️</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-red">{recordLows}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-gray bg-gray-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Total Records</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-scout-gray">{results?.total_alerts || 0}</div>
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
          <div className="grid gap-4 md:grid-cols-3">
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
                    {results?.alerts.find(a => a.property_id === propId)?.domain || propId}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block text-scout-blue">Record Type</label>
              <select
                value={selectedRecordType}
                onChange={(e) => setSelectedRecordType(e.target.value)}
                className="w-full px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
              >
                <option value="all">All Types</option>
                <option value="high">Record Highs 🏆</option>
                <option value="low">Record Lows ⚠️</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block text-scout-blue">Dimension</label>
              <select
                value={selectedDimension}
                onChange={(e) => setSelectedDimension(e.target.value)}
                className="w-full px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
              >
                <option value="all">All Dimensions</option>
                <option value="overall">Overall</option>
                <option value="device">Device</option>
                <option value="traffic_source">Traffic Source</option>
                <option value="landing_page">Landing Page</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedProperty('all');
                setSelectedRecordType('all');
                setSelectedDimension('all');
              }}
              className="border-scout-gray text-scout-gray hover:bg-scout-gray hover:text-white"
            >
              Clear Filters
            </Button>
            <span className="ml-3 text-sm text-scout-gray">
              Showing {filteredAlerts.length} of {results?.alerts.length || 0} records
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Record alerts */}
      <Card className="border-scout-blue">
        <CardHeader>
          <CardTitle className="text-scout-blue">90-Day Historical Records</CardTitle>
          <CardDescription className="text-scout-gray">
            All-time highs and lows within the past 90 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-br from-scout-blue/10 to-blue-50 rounded-lg border-2 border-scout-blue">
                <p className="text-xl font-semibold text-scout-blue">No Records Detected</p>
                <p className="text-sm text-scout-gray mt-2">No 90-day highs or lows found</p>
              </div>
            ) : (
              filteredAlerts.map((alert, index) => (
                <div
                  key={`${alert.property_id}-${alert.date}-${index}`}
                  className={`p-5 border-l-4 ${alert.record_type === 'high'
                    ? 'border-scout-green bg-green-50'
                    : 'border-scout-red bg-red-50'
                    } rounded-lg hover:opacity-90 transition-opacity shadow-sm`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {alert.record_type === 'high' ? (
                          <Trophy className="h-6 w-6 text-scout-green" />
                        ) : (
                          <TrendingDown className="h-6 w-6 text-scout-red" />
                        )}
                        <h3 className="font-bold text-scout-blue">
                          {alert.domain}
                        </h3>
                        <span className={`px-2 py-1 text-white text-xs font-semibold rounded ${alert.record_type === 'high' ? 'bg-scout-green' : 'bg-scout-red'
                          }`}>
                          {alert.record_type === 'high' ? '🏆 RECORD HIGH' : '⚠️ RECORD LOW'}
                        </span>
                        <span className="px-2 py-1 bg-scout-blue/10 text-scout-blue text-xs rounded border border-scout-blue">
                          {alert.dimension}: {alert.dimension_value}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm mt-3">
                        <div>
                          <p className="text-scout-gray">Metric</p>
                          <p className="font-semibold text-scout-blue">{alert.metric.replace(/_/g, ' ')}</p>
                        </div>
                        <div>
                          <p className="text-scout-gray">Current Value</p>
                          <p className={`font-bold text-lg ${alert.record_type === 'high' ? 'text-scout-green' : 'text-scout-red'
                            }`}>
                            {alert.value?.toLocaleString() ?? 'N/A'}
                          </p>
                        </div>
                        <div className={`p-2 rounded border ${alert.record_type === 'high' ? 'bg-scout-green/10 border-scout-green' : 'bg-scout-red/10 border-scout-red'
                          }`}>
                          <p className="text-scout-gray text-xs">Previous {alert.record_type === 'high' ? 'High' : 'Low'}</p>
                          <p className={`font-semibold ${alert.record_type === 'high' ? 'text-scout-green' : 'text-scout-red'
                            }`}>
                            {alert.previous_record?.toLocaleString() ?? 'N/A'}
                          </p>
                        </div>
                        <div className="bg-scout-blue/10 p-2 rounded border border-scout-blue">
                          <p className="text-scout-gray text-xs">Change</p>
                          <p className="font-semibold text-scout-blue">
                            {alert.record_type === 'high' 
                              ? `+${alert.increase?.toFixed(1) ?? 'N/A'}%`
                              : `${alert.decline?.toFixed(1) ?? 'N/A'}%`
                            }
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-scout-gray mt-2">
                        Detected: {new Date(alert.date).toLocaleDateString()}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-scout-blue text-scout-blue hover:bg-scout-blue hover:text-white"
                    >
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
