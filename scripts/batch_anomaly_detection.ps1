# SCOUT Batch Anomaly Detection
# [R5-R6]: Multi-method anomaly detection with business impact scoring
# Processes all properties from batch processing summary

Write-Host "SCOUT Batch Anomaly Detection" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load processing summary
$summaryFile = "data/scout_batch_processing_summary.json"
if (-not (Test-Path $summaryFile)) {
    Write-Host "ERROR: Batch summary not found. Run process_multiple_properties.ps1 first." -ForegroundColor Red
    exit 1
}

$summary = Get-Content $summaryFile | ConvertFrom-Json
$successfulProperties = $summary.results | Where-Object { $_.status -eq "success" }

Write-Host "`nAnalyzing $($successfulProperties.Count) properties for anomalies..." -ForegroundColor Yellow
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

$allAnomalies = @()
$propertyStats = @()

foreach ($property in $successfulProperties) {
    $propertyId = $property.property_id
    $domain = $property.domain
    $dataFile = $property.output_file

    Write-Host "Analyzing: $domain ($propertyId)" -ForegroundColor White

    try {
        # Load property data
        $rawData = Get-Content $dataFile | ConvertFrom-Json
        $dailyData = $rawData[0].daily_data

        if (-not $dailyData -or $dailyData.Count -lt 3) {
            Write-Host "  SKIP: Insufficient data ($($dailyData.Count) days)" -ForegroundColor Yellow
            continue
        }

        # Process each metric
        $metrics = @("users", "sessions", "page_views", "conversions")
        $propertyAnomalies = @()

        foreach ($metric in $metrics) {
            $values = $dailyData | ForEach-Object { $_.$metric }

            # Calculate statistics
            $mean = ($values | Measure-Object -Average).Average
            $count = $values.Count
            $variance = ($values | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Average).Average
            $stdev = [Math]::Sqrt($variance)

            # Calculate median and quartiles for IQR
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

            # Detect anomalies
            for ($i = 0; $i -lt $dailyData.Count; $i++) {
                $dataPoint = $dailyData[$i]
                $value = $dataPoint.$metric
                $date = $dataPoint.date

                $isAnomaly = $false
                $methods = @()

                # Z-Score method
                if ($stdev -gt 0) {
                    $zScore = [Math]::Abs(($value - $mean) / $stdev)
                    if ($zScore -gt $zScoreThreshold) {
                        $isAnomaly = $true
                        $methods += "z-score"
                    }
                }

                # IQR method
                if ($iqr -gt 0) {
                    $lowerBound = $q1 - ($iqrMultiplier * $iqr)
                    $upperBound = $q3 + ($iqrMultiplier * $iqr)
                    if ($value -lt $lowerBound -or $value -gt $upperBound) {
                        $isAnomaly = $true
                        if ($methods -notcontains "iqr") {
                            $methods += "iqr"
                        }
                    }
                }

                if ($isAnomaly) {
                    # Calculate business impact (0-100)
                    $deviation = if ($stdev -gt 0) { [Math]::Abs(($value - $mean) / $stdev) } else { 0 }
                    $direction = if ($value -lt $mean) { "drop" } else { "spike" }
                    $directionMultiplier = if ($direction -eq "drop") { 1.3 } else { 1.0 }

                    $baseImpact = [Math]::Min(100, $deviation * 25)
                    $weightedImpact = $baseImpact * $metricWeights[$metric] * $directionMultiplier
                    $finalImpact = [Math]::Min(100, [Math]::Round($weightedImpact))

                    $priority = if ($finalImpact -ge 70) { "critical" }
                                elseif ($finalImpact -ge 40) { "warning" }
                                else { "normal" }

                    $anomaly = @{
                        property_id = $propertyId
                        domain = $domain
                        date = $date
                        metric = $metric
                        value = $value
                        mean = [Math]::Round($mean, 2)
                        stdev = [Math]::Round($stdev, 2)
                        z_score = if ($stdev -gt 0) { [Math]::Round([Math]::Abs(($value - $mean) / $stdev), 2) } else { 0 }
                        direction = $direction
                        detection_methods = $methods -join ", "
                        business_impact = $finalImpact
                        priority = $priority
                    }

                    $propertyAnomalies += $anomaly
                    $allAnomalies += $anomaly
                }
            }
        }

        # Store property statistics
        $propertyStats += @{
            property_id = $propertyId
            domain = $domain
            days_analyzed = $dailyData.Count
            anomalies_found = $propertyAnomalies.Count
            critical_count = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
            warning_count = ($propertyAnomalies | Where-Object { $_.priority -eq "warning" }).Count
        }

        $criticalCount = ($propertyAnomalies | Where-Object { $_.priority -eq "critical" }).Count
        $warningCount = ($propertyAnomalies | Where-Object { $_.priority -eq "warning" }).Count

        if ($propertyAnomalies.Count -gt 0) {
            Write-Host "  ANOMALIES: $($propertyAnomalies.Count) total | Critical: $criticalCount | Warning: $warningCount" -ForegroundColor $(if ($criticalCount -gt 0) { "Red" } elseif ($warningCount -gt 0) { "Yellow" } else { "Cyan" })
        } else {
            Write-Host "  CLEAN: No anomalies detected" -ForegroundColor Green
        }

    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Generate consolidated report
$report = @{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    properties_analyzed = $successfulProperties.Count
    total_anomalies = $allAnomalies.Count
    critical_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "critical" }).Count
    warning_anomalies = ($allAnomalies | Where-Object { $_.priority -eq "warning" }).Count
    property_stats = $propertyStats
    anomalies = $allAnomalies | Sort-Object -Property business_impact -Descending
}

$reportFile = "data/scout_multi_property_anomalies.json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "ANOMALY DETECTION COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Properties Analyzed: $($successfulProperties.Count)"
Write-Host "  Total Anomalies: $($allAnomalies.Count)" -ForegroundColor Cyan
Write-Host "  Critical: $($report.critical_anomalies)" -ForegroundColor $(if ($report.critical_anomalies -gt 0) { "Red" } else { "Green" })
Write-Host "  Warning: $($report.warning_anomalies)" -ForegroundColor $(if ($report.warning_anomalies -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Report saved: $reportFile"
Write-Host "`nNext step: Review anomalies or generate alert preview"