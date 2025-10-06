# Project: SCOUT - Statistical Client Observation & Unified Tracking
Type: data-pipeline
Purpose: Automated GA4 anomaly detection system with ML insights for 50+ STM clients
Stack: BigQuery, Python, Cloud Functions, Next.js, SendGrid, Teams
Status: Implementation Active
Created: 2025-09-25

## Place-Making Specification
**Physical Metaphor**: Scout Tower / Reconnaissance Post
- Elevated observation point with 360-degree visibility
- First line of detection for approaching issues

**Signature Element**: Scout badge (three-tier alert gradient: green/yellow/red)
- Appears in every notification, dashboard, and report
- Visual consistency across all SCOUT touchpoints

**Entry Feeling**: "Protected and informed"
- Immediate confidence that SCOUT is watching
- Sense that nothing slips through

**Transformation**: Data Analyst → Pattern Hunter
- From reactive responder to proactive scout
- From manual checker to intelligence officer

**Anti-Atmosphere**: This place is NOT:
- A surveillance state (helpful, not intrusive)
- An alarm factory (intelligent, not noisy)
- A GA4 replacement (augmentation only)

## Atmosphere Requirements
- [AR1] Alert gradient visible in every communication
- [AR2] Response time feels instant for critical anomalies
- [AR3] Error messages guide toward resolution
- [AR4] Success triggers "crisis averted" satisfaction
- [AR5] Beneficial friction: Confirmation before alert dismissal

## ⚠️ CRITICAL: Always Check Dependencies First
**YOU MUST** read STATE.md before starting ANY work to see what's ready to implement.

## 🎯 Current Sprint Focus
Week 1-2: Foundation pipeline - Schema discovery and basic anomaly detection
Week 3-4: Intelligence layer - Pattern recognition and root cause analysis
Week 5-6: Advanced features - Segments and predictions

## 📚 CRITICAL: Framework Documentation Reference

### TanStack Documentation (MUST REFERENCE BEFORE CODING)
**Location**: `C:\Users\Charles Blain\CascadeProjects\docs\tanstack docs\`
- **TanStack Router**: Routing patterns, nested routes, type-safe navigation
- **TanStack Query**: Data fetching, caching, mutations, optimistic updates
- **TanStack Table**: Column definitions, filtering, sorting, pagination
- **TanStack Form**: Form validation, field management, submission handling

**Rule**: ALWAYS check TanStack docs for patterns before implementing UI features.
Never deviate from documented patterns.

## 🧪 Browser Validation Requirements (WEB UI MANDATORY)

All TanStack UI features require Chrome DevTools MCP validation.

### AI-Agent Compatible Validation (Required)
These tools return **text output** and work with all AI agents:
- `take_snapshot` → HTML text with element UIDs
- `fill_form`, `click`, `wait_for` → Interaction commands
- `list_console_messages` → Text console output
- `list_network_requests` → JSON response data
- `evaluate_script` → Returns primitives/JSON

### Human Documentation (Optional)
- `take_screenshot` → PNG images (for human review only)
- `performance_start_trace` → Performance data (AI can analyze results)

**All validation can be done without image processing.**

### ConfigTable Validation:
```markdown
BrowserTest: {
  Setup:
    - new_page → navigate to http://localhost:5179/configuration
    - take_snapshot → verify ConfigTable loaded

  AddProperty:
    - click uid="add-property-button"
    - take_snapshot → verify modal open
    - fill uid="property-id-input" value="123456789"
    - fill uid="dataset-id-input" value="analytics_123456789"
    - fill uid="client-name-input" value="Test Client"
    - fill uid="domain-input" value="example.com"
    - click uid="save-button"
    - wait_for "Property saved successfully"
    - list_console_messages → expect: no errors
    - take_screenshot → save as config-add-success.png

  Assertions:
    - Property appears in table
    - Dashboard cards update (+1 configured)
    - Data persists to Cloud Storage
}
```

### Results Dashboard Validation:
```markdown
BrowserTest: {
  Setup:
    - new_page → navigate to http://localhost:5179/results
    - take_snapshot → verify Results page loaded
    - list_network_requests resourceTypes=["fetch"]

  FilteringFlow:
    - take_snapshot → get filter dropdown UIDs
    - click uid="property-filter-dropdown"
    - click uid="property-option-249571600"
    - wait_for filtered results
    - click uid="severity-filter-dropdown"
    - click uid="severity-critical"
    - take_screenshot → filtered-critical.png
    - list_console_messages → expect: no errors

  SegmentFilter:
    - click uid="segment-type-dropdown"
    - click uid="segment-device"
    - wait_for segment badge display
    - take_screenshot → segment-device-filter.png

  Performance:
    - emulate_network "Fast 3G"
    - performance_start_trace autoStop=true, reload=true
    - performance_stop_trace
    - performance_analyze_insight "LCPBreakdown"
    - expect: LCP < 3000ms
}
```

### Navigation Flow Validation:
```markdown
BrowserTest: {
  FullUserJourney:
    - new_page → navigate to http://localhost:5179
    - take_screenshot → dashboard-home.png
    - click uid="config-nav-link"
    - wait_for "Property Configuration"
    - click uid="results-nav-link"
    - wait_for "Anomaly Results"
    - click uid="home-nav-link"
    - list_console_messages → expect: no errors
    - get_network_request url="/api/config/properties"
    - assert: status 200
}
```

## 🏗️ Architecture Decision (2025-10-01)

### System Components
1. **TanStack React UI** (Configuration & Monitoring)
   - Configure which properties to monitor
   - View anomaly detection results
   - Manage client-specific settings
   - Deploy to Vercel/Netlify

2. **Cloud Run Jobs** (Processing Pipeline)
   - Containerized Python anomaly detection scripts
   - Triggered by Cloud Scheduler (6 AM ET daily)
   - Reads config from Cloud Storage
   - Writes results to Cloud Storage

3. **Google Cloud Storage** (Data Bridge)
   - `gs://scout-config/properties.json` - UI writes configuration
   - `gs://scout-results/anomalies.json` - Jobs write results
   - `gs://scout-results/alerts/` - Historical alert archive

### Implementation Phases
**Phase 1**: UI Configuration (Current)
- Update ConfigTable to use Cloud Storage API
- Deploy frontend to Vercel
- Test configuration workflow

**Phase 2**: Cloud Run Jobs
- Containerize Python scripts with Dockerfile
- Set up Cloud Scheduler
- Configure service account permissions

**Phase 3**: Results Dashboard
- Build anomalies view in TanStack app
- Implement filtering/sorting
- Add alert history

## 📚 Project Commands
```bash
# BigQuery Testing
python scripts/test_schema_discovery.py
python scripts/test_anomaly_detection.py

# Local Development
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Cloud Run Jobs Deployment (NEW)
gcloud builds submit --tag gcr.io/stm-mvp/scout-processor
gcloud run jobs create scout-anomaly-detection \
  --image gcr.io/stm-mvp/scout-processor \
  --region us-east1
gcloud scheduler jobs create scout-daily \
  --schedule="0 6 * * *" \
  --time-zone="America/New_York" \
  --uri="https://us-east1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/stm-mvp/jobs/scout-anomaly-detection:run"

# Cloud Storage Setup
gsutil mb gs://scout-config
gsutil mb gs://scout-results
gsutil cors set cors.json gs://scout-config
```

## 🔧 Development Workflow (FOLLOW THIS EXACTLY)

### Starting a Session:
1. Check STATE.md for current progress
2. Identify next unblocked feature
3. Review BigQuery costs dashboard
4. Announce implementation plan

### For Each Feature:
1. Write BigQuery schema/query first
2. Test with single client data
3. Build Python processing logic
4. Scale test with 5 clients
5. Deploy to Cloud Function
6. Update STATE.md

## 💻 Code Standards (PRODUCTION CRITICAL)
- **SQL Queries**: Always use partitioning and clustering
- **Cost Control**: Estimate query cost before running
- **Error Handling**: Never lose anomaly data
- **Testing**: Use sandbox dataset first
- **Documentation**: Every SQL query needs cost estimate comment

## 📦 WBS Features Specification

Feature: DataIngestion {
  What:
    - "BigQuery schema discovery for all client properties" [R1]
      → provides: schema-registry
    - "Daily extraction of GA4 events data" [R2]
      → needs: schema-registry
      → provides: raw-data
    - "Handle custom conversion events dynamically" [R3]
      → needs: schema-registry
      → provides: conversion-tracking
    - "Data validation and quality checks" [R4]
      → needs: raw-data
      → provides: clean-data

  Boundaries:
    - Process data within 30 minutes for 50 clients
    - Handle up to 10M events per property daily
    - Support 100+ custom event types per client
    - Maintain 99.9% extraction success rate
    - BigQuery costs under $100/month for ingestion

  Success Criteria (Test these):
    - "[R1] working when all custom events discovered without manual config"
      → Check: `python scripts/test_schema_discovery.py --clients all`
      → Expect: ✅ All 50 clients return complete schema, 0 manual interventions
    - "[R2] validated when daily data available by 6 AM ET consistently"
      → Check: `bq query "SELECT COUNT(*) FROM processed.anomalies_daily WHERE DATE(created_at) = CURRENT_DATE() AND TIME(created_at) < '06:00:00'"`
      → Expect: ✅ Data present before 6 AM for 29/30 days (96.7% reliability)
    - "[R3] confirmed when zero data loss during extraction"
      → Check: `python scripts/validate_extraction_completeness.py --days 7`
      → Expect: ✅ 100% record count match between GA4 raw and SCOUT processed
    - "[R4] verified when schema changes handled gracefully"
      → Check: Review error logs for schema evolution events
      → Expect: ✅ Auto-adaptation logged, no pipeline failures

  Effort: ~16 hours
  Priority: CRITICAL
  Status: [ ] Not Started

  When Done:
    - Enables: All downstream analysis
    - Validates: Data pipeline reliability
    - Atmosphere: "Mission Control has full visibility"
}
Feature: AnomalyDetection {
  What:
    - "Multi-method statistical anomaly detection" [R5]
      → needs: clean-data
      → provides: raw-anomalies
    - "Business impact scoring for prioritization" [R6]
      → needs: raw-anomalies, conversion-tracking
      → provides: prioritized-alerts
    - "Cross-client pattern recognition" [R7]
      → needs: raw-anomalies
      → provides: portfolio-patterns
    - "Configurable sensitivity thresholds" [R8]
      → needs: raw-anomalies
      → provides: tuned-detection

  Boundaries:
    - Detect anomalies within 5% margin of error
    - Process 50 clients in under 10 minutes
    - Support 20+ metrics per client
    - Maximum 20% false positive rate
    - Use BigQuery ML where possible for cost efficiency

  Success Criteria (Test these):
    - "[R5] working when z-score and IQR methods both operational"
      → Check: `python scripts/test_anomaly_detection.py --methods all --clients 5`
      → Expect: ✅ Both methods complete without errors, results stored in anomalies_daily
    - "[R6] validated when 90% of real anomalies detected"
      → Check: Compare against manually flagged anomalies from first month
      → Expect: ✅ Detection rate ≥ 90% (detect 27+ of 30 known anomalies)
    - "[R7] confirmed when business impact score aligns with AM priorities"
      → Check: Survey 10 AMs on top 5 alerts from last week
      → Expect: ✅ 80% agreement that highest scored alerts were most important
    - "[R8] verified when portfolio-wide patterns identified weekly"
      → Check: `bq query "SELECT pattern_type, COUNT(*) FROM processed.patterns_portfolio WHERE week = CURRENT_WEEK() GROUP BY pattern_type"`
      → Expect: ✅ At least 3 distinct pattern types detected across clients

  Effort: ~24 hours
  Priority: CRITICAL
  Status: [ ] Not Started

  When Done:
    - Enables: Intelligent alerting system
    - Validates: Detection accuracy
    - Atmosphere: "Control room spots all threats"
}

Feature: IntelligentAlerting {
  BrowserE2ETest: {
    Scenario: "AM receives alert, investigates in dashboard"

    Steps:
      1. Simulate anomaly detection (backend script)
      2. new_page → navigate to http://localhost:5179
      3. take_snapshot → verify alert notification
      4. click uid="alert-card-0"
      5. wait_for "Anomaly Details"
      6. take_screenshot → anomaly-detail.png
      7. click uid="view-in-results"
      8. wait_for Results page with pre-filtered data
      9. list_console_messages → expect: 0 errors
      10. performance_start_trace
      11. click uid="export-csv-button"
      12. performance_stop_trace
      13. expect: Export completes < 2s

    Validation:
      - Full user journey error-free
      - Navigation between pages smooth
      - Data consistency maintained
      - Performance acceptable
  }

  What:
    - "Morning email digest with all anomalies" [R9]
      → needs: prioritized-alerts
      → provides: email-notifications
    - "Microsoft Teams integration for critical alerts" [R10]
      → needs: prioritized-alerts
      → provides: instant-alerts
    - "Root cause correlation with external factors" [R11]
      → needs: raw-anomalies, portfolio-patterns
      → provides: cause-analysis
    - "Predictive alerts for future issues" [R12]
      → needs: portfolio-patterns
      → provides: predictive-insights

  Boundaries:
    - Email delivery by 7 AM ET daily (99.9% SLA)
    - Teams alerts within 5 minutes of detection
    - 60% accuracy on root cause identification
    - 7-day prediction horizon
    - SendGrid costs under $50/month

  Success Criteria (Test these):
    - "[R9] working when AMs read email first thing Monday"
      → Check: SendGrid open rate tracking for Monday 7 AM emails
      → Expect: ✅ 85%+ open rate within 2 hours of delivery
    - "[R10] validated when critical alerts addressed within 1 hour"
      → Check: Track time between Teams alert and AM response in channel
      → Expect: ✅ Average response time < 60 minutes for critical alerts
    - "[R11] confirmed when root cause correctly identified 6/10 times"
      → Check: AM feedback survey on 20 anomalies with root cause attribution
      → Expect: ✅ 60%+ accuracy (12+ correct identifications out of 20)
    - "[R12] verified when predictions prevent at least 1 issue/month"
      → Check: Document prevented issues with before/after screenshots
      → Expect: ✅ 1+ documented case per month where prediction enabled early action

  Effort: ~20 hours
  Priority: HIGH
  Status: [ ] Not Started

  When Done:
    - Enables: Proactive client management
    - Validates: Business value delivery
    - Atmosphere: "Mission Control communicates clearly"
}

Feature: SegmentAnalysis {
  What:
    - "Dynamic segment builder interface" [R13]
      → needs: schema-registry
      → provides: segment-definitions
    - "Segment-level anomaly detection" [R14]
      → needs: segment-definitions, clean-data
      → provides: segment-anomalies
    - "Cohort behavior tracking" [R15]
      → needs: segment-definitions
      → provides: cohort-insights
    - "Segment performance predictions" [R16]
      → needs: segment-anomalies, predictive-insights
      → provides: segment-forecasts

  Boundaries:
    - Support 10 segments per client maximum
    - Process segments within daily batch window
    - Retroactive analysis up to 90 days
    - Segment size minimum 100 users
    - UI built with existing Tremor components

  Success Criteria (Test these):
    - "[R13] working when non-technical user can create segments"
      → Tool: new_page http://localhost:5179/configuration
      → Tool: take_snapshot → verify UI elements
      → Tool: click uid="add-segment-button"
      → Tool: fill_form with segment criteria
      → Tool: click uid="save-segment"
      → Tool: wait_for "Segment created"
      → Tool: list_console_messages → expect: 0 errors
      → Tool: take_screenshot → segment-created.png
      → Metric: Time to completion < 5 minutes
    - "[R14] validated when segment-specific anomalies detected"
      → Tool: navigate_page http://localhost:5179/results
      → Tool: take_snapshot → get segment filter UID
      → Tool: click uid="segment-type-dropdown"
      → Tool: click uid="segment-device"
      → Tool: wait_for segment badge visible
      → Tool: take_screenshot → segment-anomalies.png
      → Tool: evaluate_script → return document.querySelectorAll('.anomaly-card').length
      → Expect: At least 5 device-specific anomalies displayed
    - "[R15] confirmed when cohort patterns visible in dashboard"
      → Check: Visual inspection of dashboard with 2 cohorts active
      → Expect: ✅ Clear trend lines, comparison view functional, data accurate
    - "[R16] verified when predictions 70% accurate for segments"
      → Check: Compare 7-day predictions against actual for 10 segments
      → Expect: ✅ 7+ predictions within 10% margin of actual values

  Effort: ~32 hours
  Priority: MEDIUM
  Status: [ ] Not Started

  When Done:
    - Enables: Granular analysis capability
    - Validates: Advanced insights delivery
    - Atmosphere: "Deep space telemetry online"
}

## 🎯 4-Detector Anomaly System Architecture

**Critical Context**: BigQuery data has 72-hour settling period. All queries MUST use `DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)` buffer. Daily batch processing at 6 AM ET only (no real-time).

Feature: MultiDetectorAnomalySystem {
  What:
    - "Disaster detection for catastrophic failures" [R17]
      → needs: clean-data
      → provides: disaster-alerts
    - "Spam detection with quality signal analysis" [R18]
      → needs: clean-data, quality-signals
      → provides: spam-alerts
    - "Record detection for all-time highs/lows" [R19]
      → needs: historical-data-90day
      → provides: record-alerts
    - "Trend detection for directional changes" [R20]
      → needs: historical-data-180day
      → provides: trend-alerts

  Detector Specifications:

    1. DisasterDetector (P0 - Critical):
      - Algorithm: Threshold-based comparison
      - BigQuery Query: `DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)` to yesterday
      - Comparison: Yesterday vs 3-day average
      - Triggers:
        * sessions < 10 (near-zero traffic)
        * conversions = 0 (tracking failure)
        * 90%+ traffic drop from baseline
      - Dimensions: Overall ONLY (site-wide failures)
      - Output: data/scout_disaster_alerts.json
      - UI Page: /disasters (red banners, "ACT NOW" messaging)

    2. SpamDetector (P1 - High Priority):
      - Algorithm: Z-score (threshold 3.0) + quality signals
      - BigQuery Query: `DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY)` to yesterday
      - Comparison: Yesterday vs 7-day average
      - Quality Checks:
        * bounce_rate > 85%
        * avg_session_duration < 10s
      - Dimensions: Overall, Geography, Traffic Source
      - Output: data/scout_spam_alerts.json
      - UI Page: /spam (orange warnings with quality metrics)

    3. RecordDetector (P1-P3 - Mixed Priority):
      - Algorithm: Historical max/min comparison
      - BigQuery Query: `DATE_SUB(CURRENT_DATE(), INTERVAL 93 DAY)` to yesterday
      - Comparison: Yesterday vs last 90 days
      - Triggers: New high/low within 90-day window
      - Dimensions: Overall, Landing Pages, Devices, Traffic Source
      - Volume Filter: Min 100 sessions/day (high-traffic segments only)
      - Output: data/scout_record_alerts.json
      - UI Page: /records (trophy icons 🏆 for highs, ⚠️ for lows)

    4. TrendDetector (P2-P3 - Lower Priority):
      - Algorithm: Moving average crossover
      - BigQuery Query: `DATE_SUB(CURRENT_DATE(), INTERVAL 183 DAY)` to yesterday
      - Comparison: Last 30 days avg vs previous 180 days avg
      - Threshold: 15% change (up or down)
      - Dimensions: Overall, Geography, Landing Pages, Devices, Traffic Source
      - Volume Filter: Min 50 sessions/day (meaningful segments)
      - Output: data/scout_trend_alerts.json
      - UI Page: /trends (line charts with trend indicators ↗️↘️)

  Detector-Dimension Matrix (Alert Volume Control):
    Detector       | Overall | Geo  | Pages | Devices | Traffic
    ---------------|---------|------|-------|---------|----------
    Disaster (P0)  | ✅      | ❌   | ❌    | ❌      | ❌
    Spam (P1)      | ✅      | ✅   | ❌    | ❌      | ✅
    Record (P1-P3) | ✅      | ❌   | ✅    | ✅      | ✅
    Trend (P2-P3)  | ✅      | ✅   | ✅    | ✅      | ✅

  Alert Prioritization:
    P0: Disaster (tracking failure, site down)
    P1: Spam + Record Low (data quality + worst ever)
    P2: Negative Trends (gradual decline)
    P3: Positive Trends + Record High (good news)

  Boundaries:
    - Process 50 clients in under 10 minutes
    - Maximum 12 alerts per client/day
    - BigQuery costs under $150/month for all detectors
    - All data must respect 72-hour settling period
    - Daily batch processing only (6 AM ET)

  Success Criteria (Test these):
    - "[R17] working when disaster alerts catch catastrophic failures"
      → Check: `python scripts/scout_disaster_detector.py`
      → Expect: ✅ 0-3 disaster alerts per property (site-wide only)
    - "[R18] validated when spam detection identifies bot traffic"
      → Check: `python scripts/scout_spam_detector.py`
      → Expect: ✅ Quality signals present (bounce_rate, duration)
    - "[R19] confirmed when record detector finds 90-day highs/lows"
      → Check: `python scripts/scout_record_detector.py`
      → Expect: ✅ Historical context included (90-day max/min)
    - "[R20] verified when trend detector spots 30-day changes"
      → Check: `python scripts/scout_trend_detector.py`
      → Expect: ✅ Moving average comparison (30-day vs 180-day)

  Effort: ~24 hours
  Priority: HIGH
  Status: [-] In Progress

  When Done:
    - Enables: Comprehensive anomaly coverage
    - Validates: Multi-pattern detection accuracy
    - Atmosphere: "Control tower sees everything"
}

## 🚫 Anti-Requirements (DO NOT BUILD - SAVE 400+ HOURS)

### Phase 1 Exclusions
- ❌ Real-time streaming analysis (batch is sufficient)
- ❌ Client-facing dashboards (internal only)
- ❌ Historical backfill beyond 90 days
- ❌ Custom ML model training UI
- ❌ Competitor monitoring
- ❌ Attribution modeling
- ❌ Budget pacing alerts
- ❌ Custom visualization builder
- ❌ GA4 replacement features

### Technical Boundaries
- ❌ No support for non-GA4 data sources
- ❌ No automated remediation actions
- ❌ No natural language querying
- ❌ No mobile app
- ❌ No white-labeling
- ❌ No data export to client systems
- ❌ No real-time API for external systems

## 🔄 Implementation Order (Follow Dependencies!)

### Week 1-2: Foundation (Must Complete First)
1. DataIngestion.schema-registry (no dependencies) → 4 hours
2. DataIngestion.raw-data (needs: schema-registry) → 6 hours
3. DataIngestion.clean-data (needs: raw-data) → 4 hours
4. AnomalyDetection.raw-anomalies (needs: clean-data) → 8 hours

### Week 3-4: Intelligence Layer (Can Parallelize Some)
5. AnomalyDetection.prioritized-alerts (needs: raw-anomalies) → 6 hours
6. AnomalyDetection.portfolio-patterns (parallel with 5) → 8 hours
7. IntelligentAlerting.email-notifications (needs: prioritized-alerts) → 8 hours
8. IntelligentAlerting.cause-analysis (needs: portfolio-patterns) → 6 hours

### Week 5-6: Advanced Features (After Core Stable)
9. IntelligentAlerting.Teams-integration (needs: prioritized-alerts) → 4 hours
10. SegmentAnalysis.segment-builder (needs: schema-registry) → 12 hours
11. IntelligentAlerting.predictive-alerts (needs: patterns) → 8 hours
12. SegmentAnalysis.segment-anomalies (needs: segments) → 10 hours

## 📝 Session Log
<!-- Claude updates this section during work -->
### Session 1 - Project Initialization
- Created PROJECT-058-AnomalyInsights
- Defined complete WBS with dependencies
- Established Mission Control metaphor
- Ready to begin schema discovery implementation

### Next Session Goals
1. Create BigQuery dataset structure
2. Implement schema discovery function
3. Test with 3 pilot clients
