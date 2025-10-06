# SCOUT Weekly Alert Email Generator (Google Workspace)
# [R9]: Generate HTML email with weekly anomaly digest
# Uses Gmail API for zero-cost delivery

param(
    [string]$ReportFile = "data/scout_weekly_anomaly_report.json",
    [string]$OutputFile = "data/scout_weekly_alert.html"
)

Write-Host "SCOUT Weekly Alert Generator" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load anomaly report
if (-not (Test-Path $ReportFile)) {
    Write-Host "ERROR: Report file not found: $ReportFile" -ForegroundColor Red
    exit 1
}

$report = Get-Content $ReportFile | ConvertFrom-Json

Write-Host "`nLoading report data..." -ForegroundColor Yellow
Write-Host "  Properties Analyzed: $($report.properties_analyzed)"
Write-Host "  Total Anomalies: $($report.total_anomalies)"
Write-Host "  Critical: $($report.critical_anomalies)"
Write-Host "  Spam Alerts: $($report.total_spam_alerts)"

# Extract date range
$dateRange = $report.date_ranges
$analysisStart = $dateRange.analysis_start
$analysisEnd = $dateRange.analysis_end
$weekLabel = "Week of $(Get-Date $analysisStart -Format 'MMM dd') - $(Get-Date $analysisEnd -Format 'MMM dd, yyyy')"

# Get top anomalies
$criticalAnomalies = $report.anomalies | Where-Object { $_.priority -eq "critical" } | Select-Object -First 10
$warningAnomalies = $report.anomalies | Where-Object { $_.priority -eq "warning" } | Select-Object -First 5
$spamAlerts = $report.spam_alerts

# Build HTML email
$html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .email-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .header .subtitle {
            margin: 10px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }
        .scout-badge {
            display: inline-block;
            padding: 6px 12px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-size: 12px;
            margin-top: 10px;
            font-weight: 500;
        }
        .content {
            padding: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .summary-card.critical {
            border-left-color: #E74C3C;
            background: #ffebee;
        }
        .summary-card.warning {
            border-left-color: #F39C12;
            background: #fff8e1;
        }
        .summary-card.spam {
            border-left-color: #9C27B0;
            background: #f3e5f5;
        }
        .summary-card .number {
            font-size: 32px;
            font-weight: bold;
            margin: 0;
            line-height: 1;
        }
        .summary-card .label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
            display: flex;
            align-items: center;
        }
        .section-title .icon {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .section-title .icon.critical { background: #E74C3C; }
        .section-title .icon.warning { background: #F39C12; }
        .section-title .icon.spam { background: #9C27B0; }
        .anomaly-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .anomaly-card.critical {
            border-left-color: #E74C3C;
            background: #ffebee;
        }
        .anomaly-card.warning {
            border-left-color: #F39C12;
            background: #fff8e1;
        }
        .anomaly-card .header-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .anomaly-card .client-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .anomaly-card .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge.critical {
            background: #E74C3C;
            color: white;
        }
        .badge.warning {
            background: #F39C12;
            color: white;
        }
        .badge.spam {
            background: #9C27B0;
            color: white;
        }
        .anomaly-card .metric-row {
            display: flex;
            gap: 30px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .metric-row .metric-item {
            flex: 1;
            min-width: 150px;
        }
        .metric-row .metric-label {
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .metric-row .metric-value {
            font-size: 20px;
            font-weight: 600;
            color: #333;
        }
        .metric-row .metric-value.spike {
            color: #E74C3C;
        }
        .metric-row .metric-value.drop {
            color: #E74C3C;
        }
        .metric-row .metric-change {
            font-size: 12px;
            color: #666;
            margin-top: 2px;
        }
        .anomaly-card .details {
            font-size: 13px;
            color: #666;
            line-height: 1.6;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(0,0,0,0.05);
        }
        .spam-card {
            background: #f3e5f5;
            border-left: 4px solid #9C27B0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .spam-card .recommendation {
            background: white;
            padding: 12px;
            border-radius: 6px;
            margin-top: 12px;
            font-size: 13px;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        .no-anomalies {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .no-anomalies .icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header -->
        <div class="header">
            <h1>SCOUT Weekly Report</h1>
            <p class="subtitle">$weekLabel</p>
            <div class="scout-badge">Statistical Client Observation & Unified Tracking</div>
        </div>

        <!-- Content -->
        <div class="content">
            <!-- Summary Cards -->
            <div class="summary">
                <div class="summary-card">
                    <div class="number">$($report.properties_analyzed)</div>
                    <div class="label">Properties Analyzed</div>
                </div>
                <div class="summary-card critical">
                    <div class="number">$($report.critical_anomalies)</div>
                    <div class="label">Critical Anomalies</div>
                </div>
                <div class="summary-card warning">
                    <div class="number">$($report.warning_anomalies)</div>
                    <div class="label">Warning Anomalies</div>
                </div>
                <div class="summary-card spam">
                    <div class="number">$($report.total_spam_alerts)</div>
                    <div class="label">Spam Alerts</div>
                </div>
            </div>
"@

# Add spam alerts section
if ($spamAlerts -and $spamAlerts.Count -gt 0) {
    $html += @"
            <!-- Spam Alerts Section -->
            <div class="section">
                <div class="section-title">
                    <div class="icon spam"></div>
                    Spam & Bot Detection
                </div>
"@

    foreach ($spam in $spamAlerts) {
        $html += @"
                <div class="spam-card">
                    <div class="header-row">
                        <div class="client-name">$($spam.domain)</div>
                        <span class="badge spam">$($spam.risk_level) RISK</span>
                    </div>
                    <div class="metric-row">
                        <div class="metric-item">
                            <div class="metric-label">Alert Type</div>
                            <div class="metric-value">$($spam.alert_type -replace '_', ' ')</div>
                        </div>
"@
        if ($spam.country) {
            $html += @"
                        <div class="metric-item">
                            <div class="metric-label">Country</div>
                            <div class="metric-value">$($spam.country)</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Sessions</div>
                            <div class="metric-value">$($spam.total_sessions)</div>
                            <div class="metric-change">$($spam.avg_daily_sessions) per day</div>
                        </div>
"@
        }
        if ($spam.desktop_percentage) {
            $html += @"
                        <div class="metric-item">
                            <div class="metric-label">Desktop Traffic</div>
                            <div class="metric-value">$($spam.desktop_percentage)%</div>
                        </div>
"@
        }
        $html += @"
                    </div>
                    <div class="recommendation">
                        <strong>Recommendation:</strong> $($spam.recommendation)
                    </div>
                </div>
"@
    }

    $html += @"
            </div>
"@
}

# Add critical anomalies section
if ($criticalAnomalies -and $criticalAnomalies.Count -gt 0) {
    $html += @"
            <!-- Critical Anomalies Section -->
            <div class="section">
                <div class="section-title">
                    <div class="icon critical"></div>
                    Critical Anomalies (Top 10)
                </div>
"@

    foreach ($anomaly in $criticalAnomalies) {
        $changePercent = if ($anomaly.baseline_mean -gt 0) {
            [Math]::Round((($anomaly.value - $anomaly.baseline_mean) / $anomaly.baseline_mean) * 100, 1)
        } else { 0 }

        $directionSymbol = if ($anomaly.direction -eq "spike") { "▲" } else { "▼" }
        $directionClass = $anomaly.direction

        $html += @"
                <div class="anomaly-card critical">
                    <div class="header-row">
                        <div class="client-name">$($anomaly.domain)</div>
                        <span class="badge critical">CRITICAL</span>
                    </div>
                    <div class="metric-row">
                        <div class="metric-item">
                            <div class="metric-label">Metric</div>
                            <div class="metric-value">$($anomaly.metric -replace '_', ' ')</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Current Value</div>
                            <div class="metric-value $directionClass">$($anomaly.value)</div>
                            <div class="metric-change">$directionSymbol $changePercent% vs baseline</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Expected (90-day avg)</div>
                            <div class="metric-value">$($anomaly.baseline_mean)</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Impact Score</div>
                            <div class="metric-value">$($anomaly.business_impact)/100</div>
                        </div>
                    </div>
                    <div class="details">
                        <strong>Date:</strong> $(Get-Date $anomaly.date -Format 'MMM dd, yyyy') |
                        <strong>Detection:</strong> $($anomaly.detection_methods) (Z-Score: $($anomaly.z_score)) |
                        <strong>Baseline:</strong> $($anomaly.baseline_days) days
                    </div>
                </div>
"@
    }

    $html += @"
            </div>
"@
} else {
    $html += @"
            <div class="no-anomalies">
                <div class="icon">✓</div>
                <p><strong>No Critical Anomalies Detected</strong></p>
                <p>All properties performed within expected ranges this week.</p>
            </div>
"@
}

# Add warning anomalies section (collapsed/brief)
if ($warningAnomalies -and $warningAnomalies.Count -gt 0) {
    $html += @"
            <!-- Warning Anomalies Section -->
            <div class="section">
                <div class="section-title">
                    <div class="icon warning"></div>
                    Warning Anomalies (Top 5)
                </div>
"@

    foreach ($anomaly in $warningAnomalies) {
        $changePercent = if ($anomaly.baseline_mean -gt 0) {
            [Math]::Round((($anomaly.value - $anomaly.baseline_mean) / $anomaly.baseline_mean) * 100, 1)
        } else { 0 }

        $html += @"
                <div class="anomaly-card warning">
                    <div class="header-row">
                        <div class="client-name">$($anomaly.domain)</div>
                        <span class="badge warning">WARNING</span>
                    </div>
                    <div class="metric-row">
                        <div class="metric-item">
                            <div class="metric-label">Metric</div>
                            <div class="metric-value">$($anomaly.metric -replace '_', ' ')</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Date</div>
                            <div class="metric-value">$(Get-Date $anomaly.date -Format 'MMM dd')</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Change</div>
                            <div class="metric-value">$changePercent%</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Impact</div>
                            <div class="metric-value">$($anomaly.business_impact)/100</div>
                        </div>
                    </div>
                </div>
"@
    }

    $html += @"
            </div>
"@
}

# Close HTML
$html += @"
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>SCOUT</strong> - Statistical Client Observation & Unified Tracking</p>
            <p>Generated on $(Get-Date -Format 'MMMM dd, yyyy \a\t h:mm tt')</p>
            <p>Analysis Method: Weekly comparison against 90-day baseline | Data Lag Buffer: 72 hours</p>
            <p><a href="#">View Full Dashboard</a> | <a href="#">Report Issue</a></p>
        </div>
    </div>
</body>
</html>
"@

# Save HTML file
$html | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "WEEKLY ALERT GENERATED" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Report Period: $weekLabel"
Write-Host "  Critical Anomalies: $($report.critical_anomalies)" -ForegroundColor $(if ($report.critical_anomalies -gt 0) { "Red" } else { "Green" })
Write-Host "  Warning Anomalies: $($report.warning_anomalies)" -ForegroundColor $(if ($report.warning_anomalies -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Spam Alerts: $($report.total_spam_alerts)" -ForegroundColor $(if ($report.total_spam_alerts -gt 0) { "Red" } else { "Green" })
Write-Host "  HTML saved: $OutputFile"
Write-Host "`nOpen the file in a browser to preview the email."