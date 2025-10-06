# SCOUT Multi-Property Processor with Segment Analysis
# [R2-R4 + R13-R14]: Extract data with traffic source, geo, device, and landing page segments
# Enables spam detection and granular anomaly analysis

param(
    [int]$MaxProperties = 10,
    [int]$DaysBack = 7
)

Write-Host "SCOUT Segmented Data Processor" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Load available properties
$propertiesFile = "data/scout_available_properties.json"
if (-not (Test-Path $propertiesFile)) {
    Write-Host "ERROR: Properties file not found. Run discover_properties.ps1 first." -ForegroundColor Red
    exit 1
}

$allProperties = Get-Content $propertiesFile | ConvertFrom-Json
$propertiesToProcess = $allProperties | Select-Object -First $MaxProperties

Write-Host "`nProcessing $($propertiesToProcess.Count) properties with segment analysis..." -ForegroundColor Yellow
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

        # Enhanced BigQuery SQL with segmentation dimensions
        $query = @"
-- SCOUT Segmented Data Extraction [R2-R4 + R13]
-- Extracts overall metrics + segment breakdowns for spam detection

WITH daily_overall AS (
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

-- Traffic Source Segments [R13]
traffic_source_daily AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(traffic_source.source, '(direct)') as source,
        COALESCE(traffic_source.medium, '(none)') as medium,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    GROUP BY date, source, medium
    HAVING sessions > 0
),

-- Device Category Segments [R13] - Spam often from specific devices
device_daily AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(device.category, 'unknown') as device_category,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    GROUP BY date, device_category
    HAVING sessions > 0
),

-- Geography Segments [R13] - Spam often from unexpected countries
geo_daily AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        COALESCE(geo.country, 'unknown') as country,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    GROUP BY date, country
    HAVING sessions > 0
),

-- Landing Page Segments [R13]
landing_page_daily AS (
    SELECT
        PARSE_DATE('%Y%m%d', event_date) as date,
        REGEXP_EXTRACT(
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
            r'https?://[^/]+(/[^?#]*)'
        ) as landing_page,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNTIF(event_name = 'session_start') as sessions,
        COUNTIF(event_name = 'page_view') as page_views,
        COUNTIF(event_name IN ('purchase', 'conversion', 'form_submit')) as conversions
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
        AND event_name = 'page_view'
        AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') IS NOT NULL
    GROUP BY date, landing_page
    HAVING landing_page IS NOT NULL AND landing_page != '' AND page_views > 0
),

-- Domain extraction for client identification
domain_info AS (
    SELECT
        REGEXP_EXTRACT(
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
            r'https?://(?:www\.)?([^/]+)'
        ) as domain
    FROM ``st-ga4-data.analytics_$propertyId.events_*``
    WHERE _TABLE_SUFFIX BETWEEN '$startDateStr' AND '$endDateStr'
    LIMIT 1
)

-- Consolidate all segments into single output
SELECT
    '$propertyId' as property_id,
    (SELECT domain FROM domain_info LIMIT 1) as domain,

    -- Overall daily metrics
    ARRAY_AGG(
        STRUCT(date, users, sessions, page_views, conversions)
        ORDER BY date
    ) as daily_overall,

    -- Traffic source segments (top 10 by sessions)
    ARRAY(
        SELECT AS STRUCT source, medium, date, users, sessions, page_views, conversions
        FROM traffic_source_daily
        ORDER BY sessions DESC
        LIMIT 100
    ) as traffic_segments,

    -- Device segments
    ARRAY(
        SELECT AS STRUCT device_category, date, users, sessions, page_views, conversions
        FROM device_daily
        ORDER BY date, device_category
    ) as device_segments,

    -- Geography segments (top 20 countries by sessions)
    ARRAY(
        SELECT AS STRUCT country, date, users, sessions, page_views, conversions
        FROM geo_daily
        ORDER BY sessions DESC
        LIMIT 200
    ) as geo_segments,

    -- Landing page segments (top 15 pages)
    ARRAY(
        SELECT AS STRUCT landing_page, date, users, sessions, page_views, conversions
        FROM landing_page_daily
        ORDER BY sessions DESC
        LIMIT 150
    ) as landing_page_segments

FROM daily_overall
GROUP BY property_id, domain
"@

        # Execute query and save to file
        $outputFile = "data/segmented_property_$propertyId.json"
        $query | bq query --project_id=st-ga4-data --format=json --use_legacy_sql=false > $outputFile

        if ($LASTEXITCODE -eq 0) {
            $data = Get-Content $outputFile | ConvertFrom-Json

            if ($data -and $data.Count -gt 0) {
                $domain = $data[0].domain
                $dayCount = $data[0].daily_overall.Count
                $trafficSegments = $data[0].traffic_segments.Count
                $geoSegments = $data[0].geo_segments.Count
                $deviceSegments = $data[0].device_segments.Count
                $landingSegments = $data[0].landing_page_segments.Count

                Write-Host "  SUCCESS: $dayCount days" -ForegroundColor Green
                Write-Host "    Domain: $domain"
                Write-Host "    Segments: Traffic=$trafficSegments | Geo=$geoSegments | Device=$deviceSegments | Landing=$landingSegments"

                $results += @{
                    property_id    = $propertyId
                    domain         = $domain
                    days_processed = $dayCount
                    segment_counts = @{
                        traffic      = $trafficSegments
                        geo          = $geoSegments
                        device       = $deviceSegments
                        landing_page = $landingSegments
                    }
                    status         = "success"
                    output_file    = $outputFile
                }
                $successCount++
            }
            else {
                Write-Host "  WARNING: No data found" -ForegroundColor Yellow
                $results += @{
                    property_id = $propertyId
                    status      = "no_data"
                }
            }
        }
        else {
            throw "BigQuery query failed"
        }

    }
    catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            property_id = $propertyId
            status      = "error"
            error       = $_.Exception.Message
        }
        $errorCount++
    }

    Write-Host ""
}

# Save processing summary
$summary = @{
    processed_at    = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    total_attempted = $propertiesToProcess.Count
    successful      = $successCount
    errors          = $errorCount
    segment_types   = @("traffic_source", "device", "geography", "landing_page")
    results         = $results
}

$summaryFile = "data/scout_segmented_processing_summary.json"
$summary | ConvertTo-Json -Depth 10 | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "SEGMENTED PROCESSING COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60)
Write-Host "  Total Attempted: $($propertiesToProcess.Count)"
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Segment Types: Traffic Source, Device, Geography, Landing Page"
Write-Host "  Summary saved: $summaryFile"
Write-Host "`nNext step: Run segmented anomaly detection with spam indicators"
