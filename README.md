# SCOUT - Statistical Client Observation & Unified Tracking
*Your early warning system for GA4 anomalies across the entire STM portfolio*

## What is SCOUT?

SCOUT is an intelligent anomaly detection platform that monitors 50+ client GA4 properties, identifying issues before they become problems. Like a scout on reconnaissance, it's always first to spot patterns and report back with actionable intelligence.

**"SCOUT found it first, so you can fix it fast."**

## Core Capabilities

- 🔍 **Schema Discovery**: Automatically maps custom events across diverse client implementations
- ⚡ **Multi-Method Detection**: Statistical analysis (Z-score, IQR) plus ML pattern recognition  
- 📊 **Cross-Client Intelligence**: Learn from patterns across the entire portfolio
- 📧 **Smart Alerting**: Morning digests via email, critical alerts via Teams
- 🎯 **Business Impact Scoring**: Prioritizes anomalies by actual business impact

## Project Status
Currently in implementation phase. Foundation pipeline under construction.

## Tech Stack
- **Data Layer**: Google BigQuery (all client GA4 exports)
- **Processing**: Python Cloud Functions (batch daily)
- **ML/Analytics**: BigQuery ML, Statistical Analysis
- **Alerting**: SendGrid (email), Teams Webhooks
- **Dashboard**: Next.js + Tremor (Phase 2)

## Quick Start

```bash
# Clone and setup
cd "C:\Users\Charles Blain\CascadeProjects\projects\PROJECT-058-AnomalyInsights"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your BigQuery project details

# Test SCOUT's schema discovery
python scripts/scout_schema_discovery.py
```

## Documentation
- **Implementation Guide**: See QUICK_START.md
- **Technical Architecture**: See CLAUDE.local.md  
- **Progress Tracking**: See STATE.md
- **WBS & Dependencies**: See .claude/wbs-planning.md

## Project Metadata
- **Project ID**: PROJECT-058-AnomalyInsights (keeping for consistency)
- **Alias**: SCOUT
- **Type**: data-pipeline
- **Created**: 2025-09-25

---

*SCOUT: Always watching. Always ready.*