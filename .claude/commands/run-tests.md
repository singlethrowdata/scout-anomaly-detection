Execute the test suite and analyze results for: $ARGUMENTS

## 1️⃣ Run Tests
Execute tests for specified feature/file (or all if not specified):

```bash
# JavaScript/Node
npm test [filename]
npm run test:watch  # For TDD iteration
npm run test:coverage

# Python
python -m pytest tests/[filename]
python -m pytest --cov  # With coverage
python -m pytest -v  # Verbose output
```

## 2️⃣ Analyze Results

### If Tests Pass:
- Report pass rate (X/Y tests passing)
- Show coverage percentage
- Identify uncovered lines/branches
- Check performance (flag slow tests >1s)

### If Tests Fail:
- List each failing test with:
  - Test name
  - Expected vs actual result
  - Line number of failure
  - Error message/stack trace
- Analyze root cause:
  - Implementation bug?
  - Test expectation wrong?
  - Missing mock/fixture?
  - Race condition?
- Propose specific fix for each failure

## 3️⃣ Coverage Analysis
```
Current Coverage: X%
Target Coverage: 80%
Gap: Y%

Uncovered Areas:
- File.js lines 45-52: Error handling not tested
- Module.py lines 13-15: Edge case not covered
```

## 4️⃣ Suggest Additional Tests
If coverage < 80%, recommend specific test cases:

```javascript
// Suggested test for uncovered error handling
test('should handle network timeout gracefully', () => {
  // Mock network timeout
  // Verify error message
  // Check retry logic
});
```

## 5️⃣ Update STATE.md
Update test results in STATE.md:

```markdown
## 🧪 Test Coverage Tracking
Overall Coverage: X% (↑/↓ from last run)
Target Coverage: 80%

By Feature:
- Feature1: X% ✅
- Feature2: Y% 🔄
- Feature3: Z% ⚠️ (needs attention)

Recent Test Run:
- Passed: X/Y tests
- Failed: [list any failures]
- Duration: X seconds
- Last Run: [timestamp]
```

## 6️⃣ Performance Check
Flag any concerning patterns:
- Tests taking >1 second
- Test suite total time >30 seconds
- Flaky tests (inconsistent results)
- Tests with hard-coded delays

## 7️⃣ Generate Test Report
```
📊 TEST REPORT - [Feature/All]
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Passing: X tests
❌ Failing: Y tests
⏭️ Skipped: Z tests

Coverage: X% (Target: 80%)
Duration: X seconds

Critical Issues:
- [Any failing tests in critical paths]

Recommendations:
1. [Highest priority fix]
2. [Additional test needed]
3. [Performance improvement]
```

## 🎯 Next Actions
Based on results, recommend:
1. Fix failing tests first (if any)
2. Add tests for uncovered critical paths
3. Improve test performance if slow
4. Update documentation if behavior changed
