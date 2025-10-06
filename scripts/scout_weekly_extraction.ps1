# SCOUT Weekly Data Extraction with 90-Day Baseline
# [R2-R4]: Production-ready extraction with proper date handling
# Accounts for BigQuery 72-hour data lag

param(
    [int]$MaxProperties = 10,
    [switch]$AllProperties = $false
)

Write-Host "SCOUT Weekly Data Extraction (90-Day Baseline)" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Calculate date ranges accounting for 72-hour lag
$today = Get-Date
$lagDays = 4  # 72 hours + 1 day buffer

# Analysis period: Last complete week (7 days)
$analysisEndDate = $today.AddDays(-$lagDays)
$analysisStartDate = $analysisEndDate.AddDays(-6)  # 7 days total

# Baseline period: 90 days ending at analysis end
$baselineStartDate = $analysisEndDate.AddDays(-89)  # 90 days total
$baselineEndDate = $analysisEndDate

Write-Host "`nDate Configuration:" -ForegroundColor Yellow
Write-Host "  Today: $($today.ToString('yyyy-MM-dd'))"
Write-Host "  Data Lag Buffer: $lagDays days"
Write-Host ""
Write-Host "Analysis Period (Last Complete Week):"
Write-Host "  Start: $($analysisStartDate.ToString('yyyy-MM-dd'))"
Write-Host "  End:   $($analysisEndDate.ToString('yyyy-MM-dd'))"
Write-Host ""
Write-Host "Baseline Period (90-Day Historical):"
Write-Host "  Start: $($baselineStartDate.ToString('yyyy-MM-dd'))"
Write-Host "  End:   $($baselineEndDate.ToString('yyyy-MM-dd'))"
Write-Host ""

# Format dates for BigQuery
$analysisStartStr = $analysisStartDate.ToString("yyyyMMdd")
$analysisEndStr = $analysisEndDate.ToString("yyyyMMdd")
$baselineStartStr = $baselineStartDate.ToString("yyyyMMdd")
$baselineEndStr = $baselineEndDate.ToString("yyyyMMdd")

# Load available properties
$propertiesFile = "data/scout_available_properties.json"
if (-not (Test-Path $propertiesFile)) {
    Write-Host "ERROR: Properties file not found. Run discover_properties.ps1 first." -ForegroundColor Red
    exit 1
}

$allPropertiesData = Get-Content $propertiesFile | ConvertFrom-Json

if ($AllProperties) {
    $propertiesToProcess = $allPropertiesData
    Write-Host "Processing ALL $($propertiesToProcess.Count) properties..." -ForegroundColor Yellow
} else {
    $propertiesToProcess = $allPropertiesData | Select-Object -First $MaxProperties
    Write-Host "Processing $($propertiesToProcess.Count) properties..." -ForegroundColor Yellow
}

$results = @()
$successCount = 0
$errorCount = 0

foreach ($property in $propertiesToProcess) {
    $propertyId = $property.property_id
    $datasetId = $property.dataset_id

    Write-Host "`nProcessing: $propertyId" -ForegroundColor White
    Write-Host ("  " + ("-" * 55))

    try {
        # BigQuery SQL with 90-day baseline + 7-day analysis window
        $query = @"
-- SCOUT Weekly Extraction: 90-Day Baseline + Analysis Week
-- [R2-R4]: Handles 72-hour data lag, provides statistical baseline

WITH baseline_daily AS (
    -- 90 days of historical data for baseline statistics
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$baselineStartStr' AND '$baselineEndStr'
    GROUP BY event_date
),

analysis_daily AS (
    -- Last complete week for anomaly detection
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$analysisStartStr' AND '$analysisEndStr'
    GROUP BY event_date
),

-- Traffic source segments (baseline period)
traffic_baseline AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(traffic_source.source, '(direct)') as source,
        COALESCE(traffic_source.medium, '(none)') as medium,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$baselineStartStr' AND '$baselineEndStr'
    GROUP BY date, source, medium
    HAVING sessions > 0
),

-- Device segments (baseline period)
device_baseline AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(device.category, 'unknown') as device_category,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$baselineStartStr' AND '$baselineEndStr'
    GROUP BY date, device_category
    HAVING sessions > 0
),

-- Geography segments (baseline period)
geo_baseline AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(geo.country, 'unknown') as country,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$baselineStartStr' AND '$baselineEndStr'
    GROUP BY date, country
    HAVING sessions > 0
),

-- Domain extraction
domain_info AS (
    SELECT
        REGEXP_EXTRACT(
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
            r'https?://(?:www\.)?([^/]+)'
        ) as domain
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$baselineStartStr' AND '$baselineEndStr'
        AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') IS NOT NULL
    LIMIT 1
)

-- Consolidate all data
SELECT
    '$propertyId' as property_id,
    (SELECT domain FROM domain_info LIMIT 1) as domain,

    -- Data quality metadata
    STRUCT(
        '$analysisStartStr' as analysis_start,
        '$analysisEndStr' as analysis_end,
        '$baselineStartStr' as baseline_start,
        '$baselineEndStr' as baseline_end,
        (SELECT COUNT(DISTINCT date) FROM baseline_daily) as baseline_days_available,
        (SELECT COUNT(DISTINCT date) FROM analysis_daily) as analysis_days_available
    ) as data_quality,

    -- Analysis period (7 days to check)
    ARRAY_AGG(
        STRUCT(date, users, sessions, page_views, conversions)
        ORDER BY date
    ) as analysis_period,

    -- Baseline period (90 days for statistics)
    (SELECT ARRAY_AGG(STRUCT(date, users, sessions, page_views, conversions) ORDER BY date)
     FROM baseline_daily) as baseline_period,

    -- Segment data (for spam detection)
    (SELECT ARRAY_AGG(STRUCT(source, medium, date, users, sessions, page_views, conversions) ORDER BY sessions DESC LIMIT 100)
     FROM traffic_baseline) as traffic_segments,

    (SELECT ARRAY_AGG(STRUCT(device_category, date, users, sessions, page_views, conversions) ORDER BY date, device_category)
     FROM device_baseline) as device_segments,

    (SELECT ARRAY_AGG(STRUCT(country, date, users, sessions, page_views, conversions) ORDER BY sessions DESC LIMIT 200)
     FROM geo_baseline) as geo_segments

FROM analysis_daily
GROUP BY property_id, domain
"@

        # Execute query
        $outputFile = "data/weekly_property_$propertyId.json"
        $query | bq query --project_id=st-ga4-data --format=json --use_legacy_sql=false > $outputFile

        if ($LASTEXITCODE -eq 0) {
            $data = Get-Content $outputFile | ConvertFrom-Json

            if ($data -and $data.Count -gt 0) {
                $domain = $data[0].domain
                $quality = $data[0].data_quality
                $analysisDays = $data[0].analysis_period.Count
                $baselineDays = $data[0].baseline_period.Count

                # Data quality check
                $isComplete = ($analysisDays -eq 7) -and ($baselineDays -ge 80)  # Allow 10 missing days

                if ($isComplete) {
                    Write-Host "  SUCCESS: Analysis=$analysisDays days | Baseline=$baselineDays days" -ForegroundColor Green
                } else {
                    Write-Host "  WARNING: Incomplete data - Analysis=$analysisDays | Baseline=$baselineDays" -ForegroundColor Yellow
                }

                Write-Host "    Domain: $domain"
                Write-Host "    Segments: Traffic=$($data[0].traffic_segments.Count) | Geo=$($data[0].geo_segments.Count) | Device=$($data[0].device_segments.Count)"

                $results += @{
                    property_id = $propertyId
                    domain = $domain
                    analysis_days = $analysisDays
                    baseline_days = $baselineDays
                    data_complete = $isComplete
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
}

# Save processing summary
$summary = @{
    processed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    extraction_type = "weekly_90day_baseline"
    date_ranges = @{
        analysis_start = $analysisStartDate.ToString("yyyy-MM-dd")
        analysis_end = $analysisEndDate.ToString("yyyy-MM-dd")
        baseline_start = $baselineStartDate.ToString("yyyy-MM-dd")
        baseline_end = $baselineEndDate.ToString("yyyy-MM-dd")
        lag_buffer_days = $lagDays
    }
    total_attempted = $propertiesToProcess.Count
    successful = $successCount
    errors = $errorCount
    results = $results
}

$summaryFile = "data/scout_weekly_extraction_summary.json"
$summary | ConvertTo-Json -Depth 10 | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "WEEKLY EXTRACTION COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Total Attempted: $($propertiesToProcess.Count)"
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Analysis Period: $($analysisStartDate.ToString('yyyy-MM-dd')) to $($analysisEndDate.ToString('yyyy-MM-dd'))"
Write-Host "  Baseline Period: 90 days"
Write-Host "  Summary saved: $summaryFile"
Write-Host "`nNext step: Run weekly anomaly detection"