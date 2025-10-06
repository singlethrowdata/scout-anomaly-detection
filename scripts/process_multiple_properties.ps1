# SCOUT Multi-Property Batch Processor
# [R2-R6]: Process multiple GA4 properties with anomaly detection
# Run in PowerShell where gcloud is authenticated

param(
    [int]$MaxProperties = 10,
    [int]$DaysBack = 7
)

Write-Host "SCOUT Multi-Property Batch Processor" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load available properties
$propertiesFile = "data/scout_available_properties.json"
if (-not (Test-Path $propertiesFile)) {
    Write-Host "ERROR: Properties file not found. Run discover_properties.ps1 first." -ForegroundColor Red
    exit 1
}

$allProperties = Get-Content $propertiesFile | ConvertFrom-Json
$propertiesToProcess = $allProperties | Select-Object -First $MaxProperties

Write-Host "`nProcessing $($propertiesToProcess.Count) properties..." -ForegroundColor Yellow
Write-Host "Date Range: Last $DaysBack days`n"

$results = @()
$successCount = 0
$errorCount = 0

foreach ($property in $propertiesToProcess) {
    $propertyId = $property.property_id
    $datasetId = $property.dataset_id

    Write-Host "Processing: $propertyId" -ForegroundColor White
    Write-Host ("  " + ("-" * 55))

    try {
        # Calculate date range
        $endDate = Get-Date
        $startDate = $endDate.AddDays(-$DaysBack)
        $startDateStr = $startDate.ToString("yyyyMMdd")
        $endDateStr = $endDate.ToString("yyyyMMdd")

        # BigQuery SQL to extract and aggregate GA4 data
        $query = @"
WITH daily_metrics AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    GROUP BY event_date
),
domain_info AS (
    SELECT
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location' LIMIT 1) as page_url
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    LIMIT 100
)
SELECT
    '$propertyId' as property_id,
    (SELECT REGEXP_EXTRACT(page_url, r'https?://(?:www\.)?([^/]+)') FROM domain_info WHERE page_url IS NOT NULL LIMIT 1) as domain,
    ARRAY_AGG(STRUCT(date, users, sessions, page_views, conversions) ORDER BY date) as daily_data
FROM daily_metrics
GROUP BY property_id
"@

        # Execute query and save to temp file
        $outputFile = "data/temp_property_$propertyId.json"
        $query | bq query --project_id=st-ga4-data --format=json --use_legacy_sql=false > $outputFile

        if ($LASTEXITCODE -eq 0) {
            $data = Get-Content $outputFile | ConvertFrom-Json

            if ($data -and $data.Count -gt 0) {
                $domain = $data[0].domain
                $dayCount = $data[0].daily_data.Count

                Write-Host "  SUCCESS: $dayCount days | Domain: $domain" -ForegroundColor Green

                $results += @{
                    property_id = $propertyId
                    domain = $domain
                    days_processed = $dayCount
                    status = "success"
                    output_file = $outputFile
                }
                $successCount++
            } else {
                Write-Host "  WARNING: No data found" -ForegroundColor Yellow
                $results += @{
                    property_id = $propertyId
                    status = "no_data"
                }
            }
        } else {
            throw "BigQuery query failed"
        }

    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            property_id = $propertyId
            status = "error"
            error = $_.Exception.Message
        }
        $errorCount++
    }

    Write-Host ""
}

# Save processing summary
$summary = @{
    processed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    total_attempted = $propertiesToProcess.Count
    successful = $successCount
    errors = $errorCount
    results = $results
}

$summaryFile = "data/scout_batch_processing_summary.json"
$summary | ConvertTo-Json -Depth 10 | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "BATCH PROCESSING COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Total Attempted: $($propertiesToProcess.Count)"
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Summary saved: $summaryFile"
Write-Host "`nNext step: Run anomaly detection on processed properties"