# SCOUT Property Discovery Script
# Run this in PowerShell (not WSL) where gcloud is authenticated
# [R1]: Discover all GA4 properties in st-ga4-data project

Write-Host "SCOUT Property Discovery" -ForegroundColor Cyan
Write-Host ("=" * 60)

# List all datasets in st-ga4-data project
Write-Host "`nDiscovering GA4 properties..." -ForegroundColor Yellow

$datasets = bq ls --project_id=st-ga4-data --max_results=100 --format=json | ConvertFrom-Json

# Filter for analytics_* datasets (GA4 properties)
$ga4Properties = $datasets | Where-Object { $_.id -match "analytics_\d+" }

Write-Host "`nFound $($ga4Properties.Count) GA4 properties:" -ForegroundColor Green

$propertyList = @()

foreach ($dataset in $ga4Properties) {
    $propertyId = $dataset.id -replace "st-ga4-data:", "" -replace "analytics_", ""
    $propertyList += @{
        property_id = $propertyId
        dataset_id = $dataset.id
        friendly_id = $dataset.friendlyName
    }

    Write-Host "  Property: $propertyId" -ForegroundColor White
}

# Save to JSON for Python scripts to use
$outputPath = "data/scout_available_properties.json"
$propertyList | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8

Write-Host "`nSaved property list to: $outputPath" -ForegroundColor Green
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  Total GA4 Properties: $($ga4Properties.Count)"
Write-Host "  Project: st-ga4-data"
Write-Host "  Output: $outputPath"