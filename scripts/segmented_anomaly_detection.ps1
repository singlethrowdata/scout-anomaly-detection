# SCOUT Segmented Anomaly Detection with Spam Indicators
# [R5-R6 + R14]: Multi-dimensional anomaly detection with spam pattern recognition
# Detects anomalies in traffic source, geo, device, and landing page segments

Write-Host "SCOUT Segmented Anomaly Detection" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load processing summary
$summaryFile = "data/scout_segmented_processing_summary.json"
if (-not (Test-Path $summaryFile)) {
    Write-Host "ERROR: Segmented summary not found. Run process_properties_with_segments.ps1 first." -ForegroundColor Red
    exit 1
}

$summary = Get-Content $summaryFile | ConvertFrom-Json
$successfulProperties = $summary.results | Where-Object { $_.status -eq "success" }

Write-Host "`nAnalyzing $($successfulProperties.Count) properties with segment-level detection..." -ForegroundColor Yellow
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

# Spam detection patterns
$spamIndicators = @{
    # Countries with high spam probability
    spam_countries = @("Russia", "China", "India", "Pakistan", "Bangladesh", "Indonesia", "Vietnam", "Philippines")

    # Suspicious traffic sources
    spam_sources = @("buttons-for-website.com", "semalt.com", "darodar.com", "best-seo-offer.com", "lifehacĸer.com")

    # Device patterns (spam often desktop only)
    suspicious_device_pattern = "desktop_only_spike"
}

$allAnomalies = @()
$spamAlerts = @()
$propertyStats = @()

function Calculate-Statistics {
    param($values)

    if ($values.Count -lt 2) {
        return @{
            mean = 0
            stdev = 0
            median = 0
            q1 = 0
            q3 = 0
            iqr = 0
        }
    }

    $mean = ($values | Measure-Object -Average).Average
    $count = $values.Count
    $variance = ($values | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
    $stdev = [Math]::Sqrt($variance)

    $sorted = $values | Sort-Object
    $median = if ($count % 2 -eq 0) {
        ($sorted[[Math]::Floor($count/2) - 1] + $sorted[[Math]::Floor($count/2)]) / 2
    } else {
        $sorted[[Math]::Floor($count/2)]
    }

    $q1Index = [Math]::Floor($count / 4)
    $q3Index = [Math]::Floor(3 * $count / 4)
    $q1 = $sorted[$q1Index]
    $q3 = $sorted[$q3Index]
    $iqr = $q3 - $q1

    return @{
        mean = $mean
        stdev = $stdev
        median = $median
        q1 = $q1
        q3 = $q3
        iqr = $iqr
    }
}

function Detect-Anomaly {
    param(
        $value,
        $stats,
        $metric,
        $direction
    )

    $isAnomaly = $false
    $methods = @()
    $zScore = 0

    # Z-Score method
    if ($stats.stdev -gt 0) {
        $zScore = [Math]::Abs(($value - $stats.mean) / $stats.stdev)
        if ($zScore -gt $zScoreThreshold) {
            $isAnomaly = $true
            $methods += "z-score"
        }
    }

    # IQR method
    if ($stats.iqr -gt 0) {
        $lowerBound = $stats.q1 - ($iqrMultiplier * $stats.iqr)
        $upperBound = $stats.q3 + ($iqrMultiplier * $stats.iqr)
        if ($value -lt $lowerBound -or $value -gt $upperBound) {
            $isAnomaly = $true
            if ($methods -notcontains "iqr") {
                $methods += "iqr"
            }
        }
    }

    # Calculate business impact
    $deviation = if ($stats.stdev -gt 0) { [Math]::Abs(($value - $stats.mean) / $stats.stdev) } else { 0 }
    $directionMultiplier = if ($direction -eq "drop") { 1.3 } else { 1.0 }
    $baseImpact = [Math]::Min(100, $deviation * 25)
    $weightedImpact = $baseImpact * $metricWeights[$metric] * $directionMultiplier
    $finalImpact = [Math]::Min(100, [Math]::Round($weightedImpact))

    return @{
        is_anomaly = $isAnomaly
        methods = $methods -join ", "
        z_score = [Math]::Round($zScore, 2)
        business_impact = $finalImpact
        priority = if ($finalImpact -ge 70) { "critical" } elseif ($finalImpact -ge 40) { "warning" } else { "normal" }
    }
}

foreach ($property in $successfulProperties) {
    $propertyId = $property.property_id
    $domain = $property.domain
    $dataFile = $property.output_file

    Write-Host "Analyzing: $domain ($propertyId)" -ForegroundColor White

    try {
        # Load segmented data
        $rawData = Get-Content $dataFile | ConvertFrom-Json
        $propertyData = $rawData[0]

        $propertyAnomalies = @()
        $propertySpamAlerts = @()

        # 1. OVERALL METRICS (baseline detection)
        $overallData = $propertyData.daily_overall
        $metrics = @("users", "sessions", "page_views", "conversions")

        foreach ($metric in $metrics) {
            $values = $overallData | ForEach-Object { $_.$metric }
            $stats = Calculate-Statistics -values $values

            for ($i = 0; $i -lt $overallData.Count; $i++) {
                $dataPoint = $overallData[$i]
                $value = $dataPoint.$metric
                $date = $dataPoint.date
                $direction = if ($value -lt $stats.mean) { "drop" } else { "spike" }

                $result = Detect-Anomaly -value $value -stats $stats -metric $metric -direction $direction

                if ($result.is_anomaly) {
                    $propertyAnomalies += @{
                        property_id = $propertyId
                        domain = $domain
                        date = $date
                        segment_type = "overall"
                        segment_value = "all_traffic"
                        metric = $metric
                        value = $value
                        mean = [Math]::Round($stats.mean, 2)
                        detection_methods = $result.methods
                        z_score = $result.z_score
                        direction = $direction
                        business_impact = $result.business_impact
                        priority = $result.priority
                        spam_indicator = $false
                    }
                }
            }
        }

        # 2. GEOGRAPHY SEGMENTS (spam detection focus)
        $geoSegments = $propertyData.geo_segments
        if ($geoSegments -and $geoSegments.Count -gt 0) {
            # Group by country and detect anomalies
            $countrySessions = @{}
            foreach ($seg in $geoSegments) {
                $country = $seg.country
                if (-not $countrySessions.ContainsKey($country)) {
                    $countrySessions[$country] = @()
                }
                $countrySessions[$country] += $seg.sessions
            }

            # Check each country for spam patterns
            foreach ($country in $countrySessions.Keys) {
                $sessions = $countrySessions[$country]
                $totalSessions = ($sessions | Measure-Object -Sum).Sum
                $avgSessions = ($sessions | Measure-Object -Average).Average

                # Spam indicator: Known spam country + sudden spike
                $isSpamCountry = $spamIndicators.spam_countries -contains $country
                $hasSpike = $avgSessions -gt 50  # Configurable threshold

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

        # 3. DEVICE SEGMENTS (spam often desktop-heavy)
        $deviceSegments = $propertyData.device_segments
        if ($deviceSegments -and $deviceSegments.Count -gt 0) {
            # Calculate device distribution
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

                # Spam indicator: >90% desktop traffic (unusual for most sites)
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

        # 4. TRAFFIC SOURCE SEGMENTS (referral spam detection)
        $trafficSegments = $propertyData.traffic_segments
        if ($trafficSegments -and $trafficSegments.Count -gt 0) {
            foreach ($seg in $trafficSegments) {
                $source = $seg.source
                $medium = $seg.medium

                # Check for known spam sources
                $isSpamSource = $spamIndicators.spam_sources | Where-Object { $source -like "*$_*" }

                if ($isSpamSource) {
                    $propertySpamAlerts += @{
                        property_id = $propertyId
                        domain = $domain
                        alert_type = "spam_referral"
                        source = $source
                        medium = $medium
                        sessions = $seg.sessions
                        risk_level = "high"
                        recommendation = "Known spam referrer detected: $source - add to GA4 filter"
                    }
                }
            }
        }

        # Add all anomalies and spam alerts to global collections
        $allAnomalies += $propertyAnomalies
        $spamAlerts += $propertySpamAlerts

        # Property statistics
        $propertyStats += @{
            property_id = $propertyId
            domain = $domain
            anomalies_found = $propertyAnomalies.Count
            spam_alerts = $propertySpamAlerts.Count
            critical_count = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
            warning_count = ($propertyAnomalies | Where-Object { $_.priority -eq "warning" }).Count
        }

        $criticalCount = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
        $spamCount = $propertySpamAlerts.Count

        Write-Host "  Anomalies: $($propertyAnomalies.Count) | Critical: $criticalCount" -ForegroundColor $(if ($criticalCount -gt 0) { "Red" } else { "Green" })
        if ($spamCount -gt 0) {
            Write-Host "  SPAM ALERTS: $spamCount detected" -ForegroundColor Red
        }

    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
}

# Generate consolidated report
$report = @{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    properties_analyzed = $successfulProperties.Count
    total_anomalies = $allAnomalies.Count
    total_spam_alerts = $spamAlerts.Count
    critical_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "critical" }).Count
    warning_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "warning" }).Count
    property_stats = $propertyStats
    anomalies = $allAnomalies | Sort-Object -Property business_impact -Descending
    spam_alerts = $spamAlerts | Sort-Object -Property risk_level -Descending
}

$reportFile = "data/scout_segmented_anomalies_report.json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "SEGMENTED ANOMALY DETECTION COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Properties Analyzed: $($successfulProperties.Count)"
Write-Host "  Total Anomalies: $($allAnomalies.Count)" -ForegroundColor Cyan
Write-Host "  Critical: $($report.critical_anomalies)" -ForegroundColor $(if ($report.critical_anomalies -gt 0) { "Red" } else { "Green" })
Write-Host "  Warning: $($report.warning_anomalies)" -ForegroundColor $(if ($report.warning_anomalies -gt 0) { "Yellow" } else { "Green" })
Write-Host "  SPAM ALERTS: $($report.total_spam_alerts)" -ForegroundColor $(if ($report.total_spam_alerts -gt 0) { "Red" } else { "Green" })
Write-Host "  Report saved: $reportFile"
Write-Host "`nSpam detection includes: Geography, Device patterns, Known referrers"