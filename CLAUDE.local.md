# Project: AnomalyInsights
Type: data-pipeline
Purpose: Automated GA4 anomaly detection system with ML insights for 50+ STM clients
Stack: BigQuery, Python, Cloud Functions, Next.js, SendGrid, Teams
Status: Planning
Created: 2025-09-25

## Place-Making Specification
**Physical Metaphor**: [Required - What physical space is this?]
- Examples: Factory, River, Mail Sorting Facility, Refinery

**Signature Element**: [The ONE unique element that appears everywhere]
- Visual, interaction, or narrative texture that defines this place
- Examples: Oil paintings, terminal green, wood grain, constellation maps

**Entry Feeling**: [First impression in 3 words]
- Examples: "Calm and focused", "Energized and ready", "Curious and exploring"

**Transformation**: User arrives as [role/state] → leaves as [evolved role/state]
- Examples: "Analyst → Explorer", "Manager → Commander", "Sender → Cultivator"

**Anti-Atmosphere**: This place is NOT:
- [Wrong metaphor that would mislead]
- [Wrong feeling that would repel]
- [Wrong optimization that would destroy atmosphere]

## Atmosphere Requirements
- [AR1] Signature element present in: [landing, app, errors, success, docs]
- [AR2] Response time feels: [instant/thoughtful/deliberate] matching metaphor
- [AR3] Error messages feel: [helpful/protective/guiding] not harsh
- [AR4] Success moment triggers: [celebration/satisfaction/power] feeling
- [AR5] Beneficial friction at: [specify where/why we slow users down]

## ⚠️ CRITICAL: Always Check Dependencies First
**YOU MUST** read STATE.md before starting ANY work to see what's ready to implement.

## 🎯 Current Sprint Focus
[Update this each session with 1-2 key goals]

## 📚 Project Commands
\\\ash
# Testing (adjust for your project type)
# Add your test commands here
\\\

## 🔧 Development Workflow (FOLLOW THIS EXACTLY)

### Starting a Session:
1. Run \/project:wbs-status\ to see current state
2. Read STATE.md → Check what's ready to build
3. Pick highest priority unblocked feature
4. Announce what you're working on

### Implementing a Feature:
1. **Write tests FIRST** based on success criteria
2. Run tests → Verify they fail
3. Implement minimal code to pass tests
4. Refactor if needed (tests still pass)
5. Update STATE.md conversationally
6. Commit with message: \eat(FeatureName): description\

### Before Committing:
- [ ] All tests pass
- [ ] No lint errors
- [ ] STATE.md updated
- [ ] Dependencies documented

## 💻 Code Standards (IMPORTANT)
- **Line length**: Max 80 characters
- **Function size**: <50 lines, single responsibility
- **Variable names**: Descriptive (userAuthToken not token)
- **Comments**: Only for "why", not "what"
- **Error handling**: Never silently fail

## 📦 WBS Features Specification

**AWAITING WBS DEFINITION**

This project requires What-Boundaries-Success definition through Claude Code planning session.

### Expected Structure:
\\\
Feature: FeatureName {
  What:
    - "Specific requirement 1" [R1]
      → provides: capability-1
      → atmosphere: supports [metaphor element]
    - "Specific requirement 2" [R2]
      → needs: capability-1
      → provides: capability-2
      → atmosphere: includes [signature element]
  
  Boundaries:
    - Performance: "Response <200ms"
    - Scale: "100 concurrent users"
    - Tech: "Must use PostgreSQL"
    - Atmosphere: "Load time max 3s for texture"
  
  Success Criteria (Test these):
    - "User can complete X in <60 seconds"
    - "System handles Y without errors"
    - "All [R#] requirements validated"
    - "User describes feeling [intended emotion]"
  
  Effort: ~4 hours
  Priority: High
  Status: [ ] Not Started
  
  When Done:
    - Enables: [list of unblocked features]
    - Validates: [business goal]
    - Atmosphere: [transformation step achieved]
}
\\\

### Planning with Place-Making:
When defining features with Claude Code, ensure EVERY feature:
1. Exists naturally in your physical metaphor
2. Includes the signature element somewhere
3. Advances the user transformation
4. Respects beneficial friction points

## 🚫 Anti-Requirements (DO NOT BUILD)
[To be defined during planning - what's explicitly OUT of scope]

## 🔄 Implementation Order
[To be determined after WBS definition and dependency analysis]

## 📝 Session Log
<!-- Claude updates this section during work -->
