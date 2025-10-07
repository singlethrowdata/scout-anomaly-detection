import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { TrendingUp, Activity, Target, AlertTriangle, CheckCircle, Trophy, Shield } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// [R17-R20]: Load real detector data from Cloud Storage for dashboard stats
// → needs: disaster-alerts, spam-alerts, record-alerts, trend-alerts
// → provides: unified-dashboard-stats, recent-detector-alerts

interface DetectorResults {
  disasters: any;
  spam: any;
  records: any;
  trends: any;
}

export default function Index() {
  const [results, setResults] = useState<DetectorResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // [R17-R20]: Fetch all detector data from proxy server on mount
  useEffect(() => {
    fetchAllDetectors();
  }, []);

  const fetchAllDetectors = async () => {
    setLoading(true);
    setError(null);

    try {
      const [disastersRes, spamRes, recordsRes, trendsRes] = await Promise.all([
        fetch('https://storage.googleapis.com/scout-results/scout_disaster_alerts.json'),
        fetch('https://storage.googleapis.com/scout-results/scout_spam_alerts.json'),
        fetch('https://storage.googleapis.com/scout-results/scout_record_alerts.json'),
        fetch('https://storage.googleapis.com/scout-results/scout_trend_alerts.json'),
      ]);

      const [disasters, spam, records, trends] = await Promise.all([
        disastersRes.ok ? disastersRes.json() : { alerts: [] },
        spamRes.ok ? spamRes.json() : { alerts: [] },
        recordsRes.ok ? recordsRes.json() : { alerts: [] },
        trendsRes.ok ? trendsRes.json() : { alerts: [] },
      ]);

      setResults({ disasters, spam, records, trends });
    } catch (err) {
      console.error('Error fetching detector results:', err);
      setError(err instanceof Error ? err.message : 'Failed to load detector data');
    } finally {
      setLoading(false);
    }
  };

  // [R17-R20]: Calculate unified stats from all detectors
  const totalAlerts = (results?.disasters.alerts?.length || 0) +
    (results?.spam.alerts?.length || 0) +
    (results?.records.alerts?.length || 0) +
    (results?.trends.alerts?.length || 0);

  const criticalAlerts = (results?.disasters.total_alerts || 0); // P0 disasters are critical
  const recordHighs = results?.records.alerts?.filter((a: any) => a.record_type === 'high').length || 0;
  const recordLows = results?.records.alerts?.filter((a: any) => a.record_type === 'low').length || 0;

  // Get most recent timestamp across all detectors
  const lastScan = results ? [
    results.disasters.generated_at,
    results.spam.generated_at,
    results.records.generated_at,
    results.trends.generated_at,
  ].filter(Boolean).sort().reverse()[0] : '';

  // Combine recent alerts from all detectors
  const allAlerts = [
    ...(results?.disasters.alerts || []).map((a: any) => ({ ...a, detector: 'disaster', priority: 'P0' })),
    ...(results?.spam.alerts || []).map((a: any) => ({ ...a, detector: 'spam', priority: 'P1' })),
    ...(results?.records.alerts || []).map((a: any) => ({ ...a, detector: 'record', priority: a.record_type === 'low' ? 'P1' : 'P3' })),
    ...(results?.trends.alerts || []).map((a: any) => ({ ...a, detector: 'trend', priority: a.trend_direction === 'down' ? 'P2' : 'P3' })),
  ].sort((a, b) => new Date(b.detected_at || b.date).getTime() - new Date(a.detected_at || a.date).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Hero section with SCOUT mission - STM branding */}
      <div className="bg-gradient-to-r from-scout-blue to-scout-blue/90 rounded-lg shadow-lg border border-scout-blue/20 p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <Target className="w-12 h-12 text-white" />
          <div>
            <h2 className="text-3xl font-bold">SCOUT Mission Control</h2>
            <p className="text-blue-100">
              Real-time anomaly detection across {results?.disasters.properties_analyzed || 0} GA4 properties
            </p>
          </div>
        </div>
        <p className="text-blue-50 max-w-3xl">
          4-detector system monitoring your entire portfolio 24/7, detecting disasters, spam, records, and trends before clients notice.
        </p>
      </div>

      {/* Error state */}
      {error && (
        <Card className="border-scout-red/20 bg-scout-red/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-scout-red">
              <AlertTriangle className="h-5 w-5" />
              <p className="font-medium">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detector Stats Grid - STM colors */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Link to="/disasters">
          <Card className="border-scout-red/30 hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disasters (P0)</CardTitle>
              <AlertTriangle className="h-5 w-5 text-scout-red" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-scout-red">
                {loading ? '...' : criticalAlerts}
              </div>
              <p className="text-xs text-muted-foreground">Catastrophic failures</p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/spam">
          <Card className="border-orange-300 hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Spam Detected (P1)</CardTitle>
              <Shield className="h-5 w-5 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">
                {loading ? '...' : (results?.spam.total_alerts || 0)}
              </div>
              <p className="text-xs text-muted-foreground">Bot traffic identified</p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/records">
          <Card className="border-scout-green/30 hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Records (P1-P3)</CardTitle>
              <Trophy className="h-5 w-5 text-scout-green" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-scout-green">
                {loading ? '...' : `${recordHighs}🏆 ${recordLows}⚠️`}
              </div>
              <p className="text-xs text-muted-foreground">90-day highs/lows</p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/trends">
          <Card className="border-scout-blue/30 hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trends (P2-P3)</CardTitle>
              <TrendingUp className="h-5 w-5 text-scout-blue" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-scout-blue">
                {loading ? '...' : (results?.trends.total_alerts || 0)}
              </div>
              <p className="text-xs text-muted-foreground">Directional changes</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-scout-gray/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-gray">Total Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? '...' : totalAlerts}</div>
            <p className="text-xs text-muted-foreground">Across all detectors</p>
          </CardContent>
        </Card>

        <Card className="border-scout-blue/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-blue">Properties Monitored</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{loading ? '...' : (results?.disasters.properties_analyzed || 0)}</div>
            <p className="text-xs text-muted-foreground">Active monitoring</p>
          </CardContent>
        </Card>

        <Card className="border-scout-green/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-scout-green">Last Scan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold">
              {loading ? '...' : lastScan ? new Date(lastScan).toLocaleString() : 'Never'}
            </div>
            <p className="text-xs text-muted-foreground">All systems operational</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent alerts from all detectors */}
      <Card className="border-scout-blue/20">
        <CardHeader>
          <CardTitle className="text-scout-blue">Recent Alerts (All Detectors)</CardTitle>
          <CardDescription>
            Latest detected anomalies across all 4 detection systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading detector results...
            </div>
          ) : allAlerts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-2 text-scout-green" />
              <p>No anomalies detected. All systems normal!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {allAlerts.map((alert, index) => (
                <div
                  key={`${alert.property_id}-${alert.detector}-${index}`}
                  className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    {alert.detector === 'disaster' && <AlertTriangle className="h-5 w-5 text-scout-red" />}
                    {alert.detector === 'spam' && <Shield className="h-5 w-5 text-orange-600" />}
                    {alert.detector === 'record' && <Trophy className="h-5 w-5 text-scout-green" />}
                    {alert.detector === 'trend' && <TrendingUp className="h-5 w-5 text-scout-blue" />}
                    <div className="flex-1">
                      <p className="font-medium text-scout-dark">{alert.domain}</p>
                      <p className="text-sm text-scout-gray">{alert.message || alert.metric}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${alert.priority === 'P0' ? 'bg-scout-red text-white' :
                      alert.priority === 'P1' ? 'bg-orange-500 text-white' :
                        alert.priority === 'P2' ? 'bg-scout-yellow text-white' :
                          'bg-scout-green text-white'
                      }`}>
                      {alert.priority}
                    </span>
                    <Link to={`/${alert.detector}s`}>
                      <Button variant="outline" size="sm" className="border-scout-blue text-scout-blue">
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick actions */}
      <div className="flex gap-4">
        <Button
          variant="default"
          size="lg"
          onClick={fetchAllDetectors}
          className="bg-scout-blue hover:bg-scout-blue/90"
        >
          <Activity className="mr-2 h-4 w-4" />
          Refresh All Detectors
        </Button>
        <Link to="/disasters">
          <Button variant="outline" size="lg" className="border-scout-red text-scout-red">
            <AlertTriangle className="mr-2 h-4 w-4" />
            View Disasters
          </Button>
        </Link>
      </div>
    </div>
  )
}
