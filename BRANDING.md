# SCOUT Brand Guidelines
*Statistical Client Observation & Unified Tracking*

## Core Identity

### Name: SCOUT
- **Primary usage**: Always uppercase in documentation
- **In code**: Class names use Scout (ScoutDiscovery, ScoutAlert, etc.)
- **Informal**: "scout" lowercase acceptable in casual communication
- **Verb usage**: "Let me scout that data" / "SCOUT detected an anomaly"

### Tagline Options
- **Primary**: "Always watching. Always ready."
- **Alternative**: "First to know. First to warn."
- **Internal**: "SCOUT found it first, so you can fix it fast."

### Acronym Usage
- **Full expansion**: Statistical Client Observation & Unified Tracking
- **When to use**: First mention in documentation, not needed daily
- **Example**: "SCOUT (Statistical Client Observation & Unified Tracking) monitors..."

## Voice & Tone

### Personality Attributes
- **Vigilant** but not paranoid
- **Helpful** but not intrusive  
- **Confident** but not cocky
- **Professional** but approachable

### Communication Style
```
❌ AVOID: "CRITICAL SYSTEM FAILURE DETECTED!!!"
✅ PREFER: "SCOUT detected an unusual pattern that needs attention"

❌ AVOID: "Everything is fine, nothing to see here"
✅ PREFER: "SCOUT completed today's reconnaissance - no anomalies found"
```

## Visual Identity

### Color Palette (STM Brand Colors)
```css
/* PRIMARY STM COLORS */
--stm-single: #1A5276;       /* SINGLE (Blue) - Primary brand */
--stm-throw: #6B8F71;        /* THROW (Green) - Success/clear */
--stm-marketing: #6E6F71;    /* MARKETING (Gray) - Neutral/standard */

/* SCOUT ALERT LEVELS (Using STM as base) */
--scout-primary: #1A5276;    /* STM SINGLE - main interface */
--scout-success: #6B8F71;    /* STM THROW - all clear */
--scout-warning: #F39C12;    /* Alert Orange - attention needed */
--scout-danger: #E74C3C;     /* Critical Red - immediate action */
--scout-neutral: #6E6F71;    /* STM MARKETING - standard ops */

/* SEMANTIC USAGE */
--scout-normal: var(--stm-throw);      /* Normal operations */
--scout-elevated: var(--scout-warning); /* Needs attention */
--scout-critical: var(--scout-danger);  /* Urgent response */
--scout-info: var(--stm-single);       /* Informational */
--scout-muted: var(--stm-marketing);   /* Secondary text */
```

**Meta-Analysis**: 
- STM's green (THROW) is more muted than typical "success" green
- This creates sophisticated, less alarming interface
- Gray (MARKETING) perfectly suited for secondary elements
- Blue (SINGLE) already matched - good intuition or luck?

### Status Indicators (Using STM Colors)
- 🟢 **Green (#6B8F71)**: Normal operations, SCOUT reports all clear
- 🟡 **Yellow (#F39C12)**: SCOUT detected anomaly, monitoring situation
- 🔴 **Red (#E74C3C)**: Critical anomaly, SCOUT requires immediate action
- 🔵 **Blue (#1A5276)**: Informational, SCOUT intelligence update
- ⚫ **Gray (#6E6F71)**: No data / SCOUT offline / Neutral state

### ASCII Banner (for CLI tools)
```
╔═══════════════════════════════════════╗
║  SCOUT - Early Warning Intelligence   ║
║  Statistical Client Observation       ║
║  & Unified Tracking                   ║
╚═══════════════════════════════════════╝
```

## Messaging Templates

### Email Subject Lines
- ✅ "SCOUT Daily Report: 3 anomalies detected across portfolio"
- ✅ "SCOUT Alert: Critical traffic drop for [Client Name]"
- ❌ "ANOMALY DETECTED!!!" (too alarmist)

### Success Messages
- "SCOUT reconnaissance complete"
- "SCOUT identified the pattern"
- "SCOUT patrol finished successfully"

### Error Messages
- "SCOUT encountered an obstacle: [specific error]"
- "SCOUT needs assistance: [what's needed]"
- Never: "SCOUT failed" (implies total system failure)

### Teams Notifications
```
🔍 SCOUT ALERT
━━━━━━━━━━━━━
Client: [Name]
Metric: [What changed]
Severity: [Low/Medium/High]
Action: [Recommended next step]
```

## Usage in Code

### File Naming
- Scripts: `scout_[function].py`
- Classes: `ScoutDiscovery`, `ScoutAlert`, `ScoutReporter`
- Functions: `scout_analyze()`, `run_scout_patrol()`
- BigQuery: `scout_metadata`, `scout_anomalies`

### Comments Style
```python
# SCOUT: Reconnaissance beginning for client portfolio
# SCOUT: Unusual pattern detected, escalating to alert
# SCOUT: Mission complete, returning to base
```

### Log Messages
```python
logger.info("SCOUT: Beginning daily patrol")
logger.warning("SCOUT: Anomaly threshold exceeded")
logger.error("SCOUT: Unable to complete reconnaissance")
```

## Metaphor Consistency

### Military/Scout Terms to Use Appropriately
- ✅ Reconnaissance (for data scanning)
- ✅ Patrol (for scheduled runs)
- ✅ Report/Debrief (for results)
- ✅ Mission (for specific tasks)
- ✅ Territory (for client properties)

### Terms to Avoid (Too Aggressive)
- ❌ Attack, Combat, Enemy
- ❌ Weapon, Arsenal
- ❌ Casualty, Damage

## Implementation Checklist

When adding new features, ensure:
- [ ] Uses SCOUT naming convention
- [ ] Includes scout metaphor naturally
- [ ] Follows color coding for severity
- [ ] Maintains helpful, not alarmist tone
- [ ] Includes "first to know" positioning

## Examples in Context

### Morning Email Opening
```
Good morning [Name],

SCOUT completed overnight reconnaissance of your client portfolio.
Here's what deserves your attention today:
```

### Critical Alert
```
SCOUT PRIORITY ALERT
━━━━━━━━━━━━━━━━━

SCOUT detected an unusual pattern that requires immediate attention:
[Client Name] experienced a 47% traffic drop in the last 6 hours.

What SCOUT found:
• Pattern started at 2:47 AM ET
• Affects primarily mobile traffic
• Similar to previous technical issue on [date]

Recommended action:
Check GTM container for recent publishes.
```

### All Clear Message
```
SCOUT patrol complete for [Date]
All 50 client properties within normal parameters.
No anomalies detected.

Next scheduled patrol: Tomorrow 6:00 AM ET
```

## Evolution Path

As SCOUT grows, maintain:
1. The helpful scout personality (never becomes "Big Brother")
2. The "first to know" value proposition
3. The balance between vigilance and calm
4. The human-in-the-loop philosophy

---

*Remember: SCOUT is a helpful companion, not a replacement for human judgment.*
*It scouts ahead so you can make informed decisions.*