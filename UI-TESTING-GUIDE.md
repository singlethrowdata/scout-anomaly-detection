# SCOUT UI Testing Guide

## Chrome DevTools MCP Integration

### AI-Agent Compatibility Note

**All core validation is text-based and works with any AI agent:**
- `take_snapshot` returns HTML text with UIDs (not images)
- `list_console_messages` returns text console output
- `list_network_requests` returns JSON data
- `evaluate_script` returns primitives/JSON

**Only `take_screenshot` produces images** (optional, for human documentation).

### Quick Test Commands

#### Full ConfigTable Test
```bash
# In Claude Code session:
"Test the ConfigTable with Chrome DevTools:
1. new_page http://localhost:5179/configuration
2. take_snapshot and verify form elements
3. Click add property button
4. Fill form with test data
5. Submit and verify success
6. Check console for errors
7. Take screenshot of result"
```

**Expected Results:**
- ✅ All form fields accessible via UIDs
- ✅ Modal opens/closes cleanly
- ✅ Data persists to Cloud Storage
- ✅ Dashboard cards update immediately
- ✅ Zero console errors

#### Results Dashboard Test
```bash
"Test Results filtering:
1. new_page http://localhost:5179/results
2. take_snapshot to get filter UIDs
3. Test each filter dropdown (property, severity, metric, segment)
4. Verify anomalies update correctly
5. Check performance with trace
6. Screenshot final state"
```

**Expected Results:**
- ✅ All 4 filters functional
- ✅ Results update without page reload
- ✅ Filter combinations work correctly
- ✅ Segment badges display properly
- ✅ LCP < 3s on Fast 3G

#### E2E Journey Test
```bash
"Run full user journey:
1. Start at homepage
2. Navigate to configuration
3. Add new property
4. Navigate to results
5. Filter by that property
6. Export data (when implemented)
7. Return home
8. Verify no console errors
9. Check all network requests succeeded
10. Performance trace the entire journey"
```

**Expected Results:**
- ✅ Smooth navigation between pages
- ✅ State persists across navigation
- ✅ Zero console errors throughout
- ✅ All API calls return 200
- ✅ Total journey time < 10s

### TanStack Pattern Validation

Before implementing any UI feature:

1. **Check docs**: `C:\Users\Charles Blain\CascadeProjects\docs\tanstack docs\`
2. **Reference pattern**: Use exact pattern from docs
3. **Test with DevTools**: Validate behavior in browser
4. **Document**: Update STATE.md with validation results

#### TanStack Router Checks
```bash
"Validate router patterns:
1. new_page http://localhost:5179
2. Test all navigation links
3. Verify type-safe routes work
4. Check browser back/forward buttons
5. Screenshot each route"
```

#### TanStack Query Checks
```bash
"Validate data fetching:
1. new_page http://localhost:5179/configuration
2. list_network_requests to see fetch calls
3. Verify caching behavior (navigate away and back)
4. Check stale-while-revalidate pattern
5. Test error states (disconnect network)"
```

#### TanStack Table Checks
```bash
"Validate table features:
1. new_page http://localhost:5179/results
2. Test sorting on columns
3. Test filtering on all 4 dimensions
4. Verify pagination (when implemented)
5. Check row selection (when implemented)
6. Screenshot table states"
```

#### TanStack Form Checks
```bash
"Validate form features:
1. new_page http://localhost:5179/configuration
2. Click add property
3. Test field validation (empty fields)
4. Test error messages display
5. Test successful submission
6. Verify form reset after save"
```

### Performance Baselines

All UI routes must meet:
- **LCP < 2.5s** on Fast 3G
- **No console errors** during normal operation
- **API requests < 500ms** for Cloud Storage operations
- **UI interactions < 100ms** response time
- **Total bundle size < 500KB** (uncompressed)

#### Performance Test Commands
```bash
"Run performance baseline:
1. new_page http://localhost:5179
2. emulate_network 'Fast 3G'
3. emulate_cpu throttlingRate=4
4. performance_start_trace autoStop=true, reload=true
5. performance_stop_trace
6. performance_analyze_insight 'LCPBreakdown'
7. performance_analyze_insight 'DocumentLatency'
8. Screenshot performance results"
```

### Testing Checklist

**REQUIRED - AI-Agent Compatible (Text-Based):**
- [ ] **take_snapshot** confirms UI elements present with correct UIDs (returns HTML text)
- [ ] **fill_form** validates input handling and validation
- [ ] **click** verifies all interactions work smoothly
- [ ] **wait_for** confirms async operations complete
- [ ] **list_console_messages** shows 0 errors (returns text)
- [ ] **list_network_requests** shows all calls return 200 OK (returns JSON)
- [ ] **get_network_request** verifies critical API responses (returns JSON)
- [ ] **evaluate_script** confirms DOM state (returns primitives/JSON)

**OPTIONAL - Human Documentation (Images):**
- [ ] **take_screenshot** documents working state (PNG, for human review)
- [ ] **performance_start_trace** validates speed meets baseline (AI can analyze results)

### Common Test Scenarios

#### Scenario 1: Add New Property
```
new_page → take_snapshot → click add button → take_snapshot (modal) →
fill all fields → click save → wait_for success → list_console_messages →
take_screenshot → verify table updated
```

#### Scenario 2: Filter Anomalies
```
new_page /results → take_snapshot → click property filter →
select property → wait_for results → click severity filter →
select critical → take_screenshot → verify count updated
```

#### Scenario 3: Segment Analysis
```
new_page /results → take_snapshot → click segment filter →
select device → wait_for segment badges → take_screenshot →
click different segment → verify results change
```

#### Scenario 4: Navigation Flow
```
new_page / → take_screenshot → click config → wait_for config page →
click results → wait_for results page → click home →
list_console_messages → verify 0 errors
```

#### Scenario 5: Performance Under Load
```
new_page /results → emulate_network "Slow 3G" →
emulate_cpu 6 → performance_start_trace →
click all 4 filters → performance_stop_trace →
verify: still functional, LCP < 5s on slow connection
```

### Error State Testing

#### Network Failure Simulation
```bash
"Test offline behavior:
1. new_page http://localhost:5179/configuration
2. Disconnect network (browser setting)
3. Try to add property
4. Verify error message displays
5. Reconnect network
6. Verify recovery"
```

#### Invalid Data Testing
```bash
"Test validation:
1. new_page http://localhost:5179/configuration
2. Click add property
3. Fill invalid property ID (letters instead of numbers)
4. Try to save
5. Verify validation error shows
6. Screenshot error state"
```

### Debugging with DevTools

When a test fails:

1. **Check console first**: `list_console_messages`
2. **Check network**: `list_network_requests` with filters
3. **Check performance**: `performance_start_trace` to find bottlenecks
4. **Take snapshot**: Verify DOM state with `take_snapshot`
5. **Evaluate script**: Use `evaluate_script` to inspect variables
6. **Screenshot**: Document the failure state

### CI/CD Integration (Future)

These DevTools tests should eventually run:
- On every commit (smoke tests)
- On pull requests (full suite)
- Nightly (performance regressions)
- Pre-deployment (critical paths)

### Test Coverage Goals

- **ConfigTable**: 100% of CRUD operations
- **Results Dashboard**: 100% of filter combinations
- **Navigation**: 100% of routes
- **Error States**: 100% of user-facing errors
- **Performance**: 100% of critical user paths

### Documentation Requirements

After each test session, update STATE.md with:
- ✅/❌ Test results
- Screenshot filenames
- Performance metrics
- Any discovered issues
- TanStack patterns validated

---

**Remember**: DevTools validation is MANDATORY for all UI features.
"It works on my machine" is not sufficient - prove it with DevTools tests.
