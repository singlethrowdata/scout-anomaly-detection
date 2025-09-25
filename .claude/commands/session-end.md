Perform end-of-session cleanup and prepare handoff for next session.

## 1️⃣ Commit Outstanding Changes
- Check git status
- Stage all completed work
- Create descriptive commit messages
- Push to remote repository

## 2️⃣ Update STATE.md Comprehensively

### Update In-Progress Section:
- Mark exact stopping point
- Note what line/function you were on
- Document any half-finished work
- List failing tests that need fixing

### Update Session Notes:
```markdown
### [Current Date/Time] - Session End
- **Accomplished**: [specific completed items]
- **Time Spent**: X hours
- **Velocity**: X features/hour
- **Blocked By**: [any blockers encountered]
- **Discovered**: [new requirements or issues]
- **Next Steps**: [specific next actions]
```

### Update Next Session Priority:
1. Most critical unblocked task
2. Reason for prioritization
3. Estimated time to complete

## 3️⃣ Run Final Test Suite
```bash
npm test  # or python -m pytest
```
- Document test results in STATE.md
- Note any new test failures
- Update coverage percentage

## 4️⃣ Update CLAUDE.local.md Session Log
Add entry:
```markdown
### [Date/Time]
- Completed: [features/tasks]
- Decisions: [technical choices made]
- Learnings: [what to remember]
```

## 5️⃣ Check Dependencies
- Review if any new dependencies discovered
- Update feature dependency notes
- Note newly unblocked features

## 6️⃣ Create Handoff Summary
Generate clear handoff message:

```
📋 SESSION SUMMARY - [Date]
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Completed:
- [Feature/task 1] (X hours)
- [Feature/task 2] (Y hours)

🔄 In Progress:
- [Feature] - X% complete, stopped at [specific point]

⏭️ Next Session Should:
1. [Specific next task]
2. [Why this is next]
3. [Expected outcome]

⚠️ Important Context:
- [Any critical info for next session]
- [Decisions that were made]
- [Blockers to be aware of]

📊 Metrics:
- Session Duration: X hours
- Features Completed: X
- Test Coverage: X%
- Velocity: X features/hour
```

## 7️⃣ Final Git Push
```bash
git add .
git commit -m "session: end of session [date] - summary"
git push
```

## 8️⃣ Verify Everything Saved
- Confirm all files saved
- Verify git push succeeded
- Check no uncommitted changes
- Ensure STATE.md is current

✅ Session properly closed and ready for handoff!
