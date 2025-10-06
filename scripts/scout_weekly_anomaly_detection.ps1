# SCOUT Weekly Anomaly Detection (90-Day Baseline)
# [R5-R6]: Production anomaly detection comparing last week vs 90-day baseline
# Proper statistical methodology for reliable detection

Write-Host "SCOUT Weekly Anomaly Detection (90-Day Baseline)" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load extraction summary
$summaryFile = "data/scout_weekly_extraction_summary.json"
if (-not (Test-Path $summaryFile)) {
    Write-Host "ERROR: Extraction summary not found. Run scout_weekly_extraction.ps1 first." -ForegroundColor Red
    exit 1
}

$summary = Get-Content $summaryFile | ConvertFrom-Json
$successfulProperties = $summary.results | Where-Object { $_.status -eq "success" -and $_.data_complete -eq $true }

Write-Host "`nAnalyzing $($successfulProperties.Count) properties with complete data..." -ForegroundColor Yellow
Write-Host "Analysis Period: $($summary.date_ranges.analysis_start) to $($summary.date_ranges.analysis_end)"
Write-Host "Baseline Period: $($summary.date_ranges.baseline_start) to $($summary.date_ranges.baseline_end)"
Write-Host ""

# Statistical thresholds
$zScoreThreshold = 2.0
$iqrMultiplier = 1.5

# Business impact weights
$metricWeights = @{
    conversions = 2.0
    users = 1.2
    sessions = 1.0
    page_views = 0.8
}

# Spam indicators
$spamCountries = @("Russia", "China", "India", "Pakistan", "Bangladesh", "Indonesia", "Vietnam", "Philippines")
$spamSources = @("buttons-for-website.com", "semalt.com", "darodar.com", "best-seo-offer.com", "lifehacĸer.com")

$allAnomalies = @()
$spamAlerts = @()
$propertyStats = @()

function Calculate-BaselineStatistics {
    param($baselineData, $metric)

    $values = $baselineData | ForEach-Object { $_.$metric }

    if ($values.Count -lt 10) {
        return $null
    }

    $mean = ($values | Measure-Object -Average).Average
    $count = $values.Count
    $variance = ($values | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
    $stdev = [Math]::Sqrt($variance)

    $sorted = $values | Sort-Object
    $q1Index = [Math]::Floor($count / 4)
    $q3Index = [Math]::Floor(3 * $count / 4)
    $q1 = $sorted[$q1Index]
    $q3 = $sorted[$q3Index]
    $iqr = $q3 - $q1

    return @{
        mean = $mean
        stdev = $stdev
        q1 = $q1
        q3 = $q3
        iqr = $iqr
        count = $count
    }
}

function Test-Anomaly {
    param(
        $value,
        $baseline,
        $metric
    )

    if (-not $baseline) {
        return $null
    }

    $isAnomaly = $false
    $methods = @()
    $zScore = 0

    # Z-Score method
    if ($baseline.stdev -gt 0) {
        $zScore = [Math]::Abs(($value - $baseline.mean) / $baseline.stdev)
        if ($zScore -gt $zScoreThreshold) {
            $isAnomaly = $true
            $methods += "z-score"
        }
    }

    # IQR method
    if ($baseline.iqr -gt 0) {
        $lowerBound = $baseline.q1 - ($iqrMultiplier * $baseline.iqr)
        $upperBound = $baseline.q3 + ($iqrMultiplier * $baseline.iqr)
        if ($value -lt $lowerBound -or $value -gt $upperBound) {
            $isAnomaly = $true
            if ($methods -notcontains "iqr") {
                $methods += "iqr"
            }
        }
    }

    $direction = if ($value -lt $baseline.mean) { "drop" } else { "spike" }

    # Calculate business impact
    $deviation = if ($baseline.stdev -gt 0) { [Math]::Abs(($value - $baseline.mean) / $baseline.stdev) } else { 0 }
    $directionMultiplier = if ($direction -eq "drop") { 1.3 } else { 1.0 }
    $baseImpact = [Math]::Min(100, $deviation * 25)
    $weightedImpact = $baseImpact * $metricWeights[$metric] * $directionMultiplier
    $finalImpact = [Math]::Min(100, [Math]::Round($weightedImpact))

    return @{
        is_anomaly = $isAnomaly
        methods = $methods -join ", "
        z_score = [Math]::Round($zScore, 2)
        direction = $direction
        business_impact = $finalImpact
        priority = if ($finalImpact -ge 70) { "critical" } elseif ($finalImpact -ge 40) { "warning" } else { "normal" }
        baseline_mean = [Math]::Round($baseline.mean, 2)
        baseline_stdev = [Math]::Round($baseline.stdev, 2)
    }
}

foreach ($property in $successfulProperties) {
    $propertyId = $property.property_id
    $domain = $property.domain
    $dataFile = $property.output_file

    Write-Host "Analyzing: $domain ($propertyId)" -ForegroundColor White

    try {
        $rawData = Get-Content $dataFile | ConvertFrom-Json
        $propertyData = $rawData[0]

        $analysisData = $propertyData.analysis_period
        $baselineData = $propertyData.baseline_period

        $propertyAnomalies = @()
        $propertySpamAlerts = @()

        # Metrics to analyze
        $metrics = @("users", "sessions", "page_views", "conversions")

        foreach ($metric in $metrics) {
            # Calculate baseline statistics from 90 days
            $baseline = Calculate-BaselineStatistics -baselineData $baselineData -metric $metric

            if (-not $baseline) {
                Write-Host "  SKIP: Insufficient baseline data for $metric" -ForegroundColor Yellow
                continue
            }

            # Test each day in analysis period against baseline
            foreach ($dataPoint in $analysisData) {
                $value = $dataPoint.$metric
                $date = $dataPoint.date

                $result = Test-Anomaly -value $value -baseline $baseline -metric $metric

                if ($result -and $result.is_anomaly) {
                    $propertyAnomalies += @{
                        property_id = $propertyId
                        domain = $domain
                        date = $date
                        metric = $metric
                        value = $value
                        baseline_mean = $result.baseline_mean
                        baseline_stdev = $result.baseline_stdev
                        baseline_days = $baseline.count
                        z_score = $result.z_score
                        direction = $result.direction
                        detection_methods = $result.methods
                        business_impact = $result.business_impact
                        priority = $result.priority
                    }
                }
            }
        }

        # SPAM DETECTION: Geography patterns
        $geoSegments = $propertyData.geo_segments
        if ($geoSegments -and $geoSegments.Count -gt 0) {
            $countrySessions = @{}
            foreach ($seg in $geoSegments) {
                $country = $seg.country
                if (-not $countrySessions.ContainsKey($country)) {
                    $countrySessions[$country] = @()
                }
                $countrySessions[$country] += $seg.sessions
            }

            foreach ($country in $countrySessions.Keys) {
                $sessions = $countrySessions[$country]
                $totalSessions = ($sessions | Measure-Object -Sum).Sum
                $avgSessions = ($sessions | Measure-Object -Average).Average

                $isSpamCountry = $spamCountries -contains $country
                $hasSpike = $avgSessions -gt 50

                if ($isSpamCountry -and $hasSpike) {
                    $propertySpamAlerts += @{
                        property_id = $propertyId
                        domain = $domain
                        alert_type = "spam_geography"
                        country = $country
                        total_sessions = $totalSessions
                        avg_daily_sessions = [Math]::Round($avgSessions, 2)
                        risk_level = "high"
                        recommendation = "Review traffic from $country - common spam source with elevated activity"
                    }
                }
            }
        }

        # SPAM DETECTION: Device patterns
        $deviceSegments = $propertyData.device_segments
        if ($deviceSegments -and $deviceSegments.Count -gt 0) {
            $deviceTotals = @{}
            foreach ($seg in $deviceSegments) {
                $device = $seg.device_category
                if (-not $deviceTotals.ContainsKey($device)) {
                    $deviceTotals[$device] = 0
                }
                $deviceTotals[$device] += $seg.sessions
            }

            $totalSessions = ($deviceTotals.Values | Measure-Object -Sum).Sum
            if ($totalSessions -gt 0) {
                $desktopPct = if ($deviceTotals.ContainsKey("desktop")) {
                    ($deviceTotals["desktop"] / $totalSessions) * 100
                } else { 0 }

                if ($desktopPct -gt 90) {
                    $propertySpamAlerts += @{
                        property_id = $propertyId
                        domain = $domain
                        alert_type = "spam_device"
                        desktop_percentage = [Math]::Round($desktopPct, 1)
                        risk_level = "medium"
                        recommendation = "Unusually high desktop traffic ($([Math]::Round($desktopPct, 1))%) - investigate for bot activity"
                    }
                }
            }
        }

        # SPAM DETECTION: Traffic sources
        $trafficSegments = $propertyData.traffic_segments
        if ($trafficSegments -and $trafficSegments.Count -gt 0) {
            foreach ($seg in $trafficSegments) {
                $source = $seg.source
                $isSpamSource = $spamSources | Where-Object { $source -like "*$_*" }

                if ($isSpamSource) {
                    $propertySpamAlerts += @{
                        property_id = $propertyId
                        domain = $domain
                        alert_type = "spam_referral"
                        source = $source
                        medium = $seg.medium
                        sessions = $seg.sessions
                        risk_level = "high"
                        recommendation = "Known spam referrer detected: $source - add to GA4 filter"
                    }
                }
            }
        }

        $allAnomalies += $propertyAnomalies
        $spamAlerts += $propertySpamAlerts

        $propertyStats += @{
            property_id = $propertyId
            domain = $domain
            analysis_days = $analysisData.Count
            baseline_days = $baselineData.Count
            anomalies_found = $propertyAnomalies.Count
            spam_alerts = $propertySpamAlerts.Count
            critical_count = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
            warning_count = ($propertyAnomalies | Where-Object { $_.priority -eq "warning" }).Count
        }

        $criticalCount = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
        $warningCount = ($propertyAnomalies | Where-Object { $_.priority -eq "warning" }).Count
        $spamCount = $propertySpamAlerts.Count

        Write-Host "  Anomalies: $($propertyAnomalies.Count) | Critical: $criticalCount | Warning: $warningCount" -ForegroundColor $(if ($criticalCount -gt 0) { "Red" } elseif ($warningCount -gt 0) { "Yellow" } else { "Green" })
        if ($spamCount -gt 0) {
            Write-Host "  SPAM: $spamCount alerts" -ForegroundColor Red
        }

    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
}

# Generate consolidated report
$report = @{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    detection_method = "weekly_90day_baseline"
    date_ranges = $summary.date_ranges
    properties_analyzed = $successfulProperties.Count
    total_anomalies = $allAnomalies.Count
    total_spam_alerts = $spamAlerts.Count
    critical_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "critical" }).Count
    warning_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "warning" }).Count
    property_stats = $propertyStats
    anomalies = $allAnomalies | Sort-Object -Property business_impact -Descending
    spam_alerts = $spamAlerts | Sort-Object -Property risk_level -Descending
}

$reportFile = "data/scout_weekly_anomaly_report.json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "WEEKLY ANOMALY DETECTION COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Properties Analyzed: $($successfulProperties.Count)"
Write-Host "  Total Anomalies: $($allAnomalies.Count)" -ForegroundColor Cyan
Write-Host "  Critical: $($report.critical_anomalies)" -ForegroundColor $(if ($report.critical_anomalies -gt 0) { "Red" } else { "Green" })
Write-Host "  Warning: $($report.warning_anomalies)" -ForegroundColor $(if ($report.warning_anomalies -gt 0) { "Yellow" } else { "Green" })
Write-Host "  SPAM Alerts: $($report.total_spam_alerts)" -ForegroundColor $(if ($report.total_spam_alerts -gt 0) { "Red" } else { "Green" })
Write-Host "  Report saved: $reportFile"
Write-Host "`nMethod: Last week compared against 90-day baseline"
Write-Host "Data Lag: 72-hour buffer applied"
Write-Host "`nNext step: Generate email alert preview"