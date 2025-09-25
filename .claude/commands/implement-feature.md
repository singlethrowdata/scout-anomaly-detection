Implement the feature: $ARGUMENTS

Follow this EXACT test-driven development process:

## 1️⃣ Pre-Implementation Check
- Read CLAUDE.local.md to understand the feature requirements [R#]
- Check STATE.md to verify ALL dependencies are met
- If any dependency missing, STOP and report what's blocking

## 2️⃣ Write Tests FIRST (Required!)
Write comprehensive tests covering:
- Each requirement [R#] from the WBS
- Happy path scenarios
- Edge cases and boundaries  
- Error conditions
- Performance requirements (if specified)
- Integration points

Create test file: `test_[feature_name].py` or `[feature].test.js`

## 3️⃣ Verify Tests Fail
- Run the test suite
- Confirm ALL new tests fail appropriately
- This proves we're testing the right things

## 4️⃣ Implement Minimum Code
- Write ONLY enough code to make tests pass
- No extra features or "nice to haves"
- Follow code standards from CLAUDE.local.md
- Keep functions under 50 lines

## 5️⃣ Make Tests Pass
- Run tests iteratively
- Fix implementation until all tests green
- Don't modify tests to make them pass (fix the code!)

## 6️⃣ Refactor (if needed)
- Once tests pass, refactor for clarity
- Ensure tests still pass after refactoring
- Check line length, function size, naming

## 7️⃣ Update STATE.md
Update with:
```markdown
### [Feature Name]
- **Status**: 🔄 X% Complete (~X hours spent)
- **Tests**: X/X passing
- **Provides**: `capability-name`
- **Notes**: [any discoveries or decisions]
```

## 8️⃣ Commit Changes
Create descriptive commit:
```
feat(FeatureName): implement [what it does]

- Satisfies requirements [R1], [R2], [R3]
- All tests passing (X tests)
- Provides: capability-name
- Enables: next-feature

Time spent: X hours
```

## ⚠️ IMPORTANT
- DO NOT write implementation before tests exist
- DO NOT skip the test failure verification
- DO NOT add features beyond the requirements
- DO follow TDD strictly - it ensures correctness

If you deviate from TDD, stop and start over.
