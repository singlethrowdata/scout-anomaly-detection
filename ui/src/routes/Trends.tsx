// [R20]: Trend Detection Dashboard - P2-P3 Directional Changes
// → needs: trend-alerts from Cloud Storage
// → provides: trend-monitoring, moving-average-ui
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { TrendingUp, TrendingDown, RefreshCw, Download, Filter } from 'lucide-react';

// [R20]: Trend alert data structure
interface TrendAlert {
  property_id: string;
  property_name?: string;
  domain: string;
  date: string;
  detected_at?: string;
  dimension: 'overall' | 'geography' | 'device' | 'traffic_source';
  dimension_value: string;
  metric: string;
  trend_direction: 'up' | 'down';
  percent_change: number;
  current_30day_avg: number;
  baseline_180day_avg: number;
  priority: 'warning' | 'normal';
}

interface TrendResults {
  generated_at: string;
  timestamp?: string;
  properties_analyzed: number;
  total_trends: number;
  upward_trends: number;
  downward_trends: number;
  alerts: TrendAlert[];
}

export default function Trends() {
  const [results, setResults] = useState<TrendResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<string>('all');
  const [selectedDirection, setSelectedDirection] = useState<string>('all');
  const [selectedDimension, setSelectedDimension] = useState<string>('all');

  // [R20]: Load trend alerts from Cloud Storage via proxy
  const loadResults = async () => {
    setLoading(true);
    setError(null);
    try {
      // Add cache-busting to bypass CDN cache
      const response = await fetch(`https://storage.googleapis.com/scout-results/scout_trend_alerts.json?t=${Date.now()}`);
      if (!response.ok) {
        throw new Error('Failed to load trend alerts');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trend alerts');
      console.error('Error loading trends:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  const filteredAlerts = results?.alerts.filter(alert => {
    if (selectedProperty !== 'all' && alert.property_id !== selectedProperty) return false;
    if (selectedDirection !== 'all' && alert.trend_direction !== selectedDirection) return false;
    if (selectedDimension !== 'all' && alert.dimension !== selectedDimension) return false;
    return true;
  }) || [];

  const uniqueProperties = [...new Set(results?.alerts.map(a => a.property_id) || [])];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-scout-blue mx-auto mb-4" />
          <p className="text-scout-gray">Loading trend detection results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md border-scout-blue">
          <CardHeader>
            <CardTitle className="text-scout-blue">Error Loading Trends</CardTitle>
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
          <TrendingUp className="w-12 h-12 text-white" />
          <div>
            <h2 className="text-3xl font-bold">📈 Trend Detection</h2>
            <p className="text-blue-100">P2-P3 Directional Changes - Moving Average Analysis</p>
          </div>
        </div>
        <p className="text-blue-50 max-w-3xl">
          Detects 30-day vs 180-day moving average crossovers (15% threshold) across all dimensions. Identifies upward and downward trends across geography, devices, traffic sources, and landing pages for strategic decision-making.
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
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-scout-blue bg-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Properties Monitored</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-scout-blue">{uniqueProperties.length || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-green bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Upward Trends ↗️</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-green">{results?.alerts?.filter((a: any) => a.trend_direction === 'up').length || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-yellow bg-yellow-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Downward Trends ↘️</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-yellow">{results?.alerts?.filter((a: any) => a.trend_direction === 'down').length || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-scout-gray bg-gray-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Total Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-scout-gray">{results?.alerts?.length || 0}</div>
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
                    {results?.alerts.find(a => a.property_id === propId)?.property_name || results?.alerts.find(a => a.property_id === propId)?.domain || propId}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block text-scout-blue">Trend Direction</label>
              <select
                value={selectedDirection}
                onChange={(e) => setSelectedDirection(e.target.value)}
                className="w-full px-3 py-2 border border-scout-gray rounded-md focus:border-scout-blue focus:outline-none"
              >
                <option value="all">All Directions</option>
                <option value="up">Upward ↗️</option>
                <option value="down">Downward ↘️</option>
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
                <option value="geography">Geography</option>
                <option value="device">Device</option>
                <option value="traffic_source">Traffic Source</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedProperty('all');
                setSelectedDirection('all');
                setSelectedDimension('all');
              }}
              className="border-scout-gray text-scout-gray hover:bg-scout-gray hover:text-white"
            >
              Clear Filters
            </Button>
            <span className="ml-3 text-sm text-scout-gray">
              Showing {filteredAlerts.length} of {results?.alerts.length || 0} trends
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Trend alerts */}
      <Card className="border-scout-blue">
        <CardHeader>
          <CardTitle className="text-scout-blue">Directional Change Detection</CardTitle>
          <CardDescription className="text-scout-gray">
            30-day vs 180-day moving average crossover analysis (15% threshold)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-br from-scout-blue/10 to-blue-50 rounded-lg border-2 border-scout-blue">
                <p className="text-xl font-semibold text-scout-blue">No Significant Trends</p>
                <p className="text-sm text-scout-gray mt-2">No 15%+ directional changes detected</p>
              </div>
            ) : (
              filteredAlerts.map((alert, index) => (
                <div
                  key={`${alert.property_id}-${alert.date}-${index}`}
                  className={`p-5 border-l-4 ${alert.trend_direction === 'up'
                    ? 'border-scout-green bg-green-50'
                    : 'border-scout-yellow bg-yellow-50'
                    } rounded-lg hover:opacity-90 transition-opacity shadow-sm`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {alert.trend_direction === 'up' ? (
                          <TrendingUp className="h-6 w-6 text-scout-green" />
                        ) : (
                          <TrendingDown className="h-6 w-6 text-scout-yellow" />
                        )}
                        <h3 className="font-bold text-scout-blue">
                          {alert.property_name || alert.domain || alert.property_id}
                        </h3>
                        <span className={`px-2 py-1 text-white text-xs font-semibold rounded ${alert.trend_direction === 'up' ? 'bg-scout-green' : 'bg-scout-yellow'
                          }`}>
                          {alert.trend_direction === 'up' ? '↗️ UPWARD' : '↘️ DOWNWARD'}
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
                          <p className="text-scout-gray">Percent Change</p>
                          <p className={`font-bold text-lg ${alert.trend_direction === 'up' ? 'text-scout-green' : 'text-scout-yellow'
                            }`}>
                            {alert.trend_direction === 'up' ? '+' : ''}{alert.percent_change.toFixed(1)}%
                          </p>
                        </div>
                        <div className={`p-2 rounded border ${alert.trend_direction === 'up' ? 'bg-scout-green/10 border-scout-green' : 'bg-scout-yellow/10 border-scout-yellow'
                          }`}>
                          <p className="text-scout-gray text-xs">30-Day Avg (Recent)</p>
                          <p className={`font-bold ${alert.trend_direction === 'up' ? 'text-scout-green' : 'text-scout-yellow'
                            }`}>
                            {alert.current_30day_avg ? alert.current_30day_avg.toLocaleString() : 'N/A'}
                          </p>
                        </div>
                        <div className="bg-scout-gray/10 p-2 rounded border border-scout-gray">
                          <p className="text-scout-gray text-xs">180-Day Avg (Baseline)</p>
                          <p className="font-semibold text-scout-gray">
                            {alert.baseline_180day_avg ? alert.baseline_180day_avg.toLocaleString() : 'N/A'}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-scout-gray mt-2">
                        Detected: {new Date(alert.detected_at || alert.date).toLocaleDateString()}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-scout-blue text-scout-blue hover:bg-scout-blue hover:text-white"
                    >
                      Analyze
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
