Analyze and resolve current blockers preventing progress.

## 1️⃣ Identify All Blockers
From STATE.md, list all blocked features:

```markdown
Currently Blocked:
1. [Feature Name] - Blocked by: [specific dependency]
2. [Feature Name] - Blocked by: [missing service]
3. [Feature Name] - Blocked by: [external factor]
```

## 2️⃣ Analyze Each Blocker

For each blocked item, determine:

### Type of Blocker:
- **Hard Dependency**: Must wait for another feature
- **Soft Dependency**: Could work around temporarily  
- **External**: Waiting for API key, service, approval
- **Technical**: Missing knowledge or tool
- **Misconfigured**: Wrong assumption about dependency

### Can We Unblock Now?
- ✅ Yes - How?
- ⚠️ Partially - What subset can we do?
- ❌ No - What exactly do we need?

## 3️⃣ Resolution Strategies

### For Hard Dependencies:
```markdown
Feature X blocked by Feature Y:
- Check if Feature Y is truly needed
- Can we mock/stub Feature Y temporarily?
- Can we implement a subset without Y?
- Should we prioritize completing Y?
```

### For Soft Dependencies:
```markdown
Temporary workaround:
1. Create mock/stub implementation
2. Use hardcoded data temporarily
3. Build interface now, implementation later
4. Document what needs updating when dependency ready
```

### For External Blockers:
```markdown
Missing external service/API:
1. Use mock service for development
2. Create fake data generator
3. Build everything except integration
4. Document integration points for later
```

### For Technical Blockers:
```markdown
Missing knowledge/tool:
1. Research solution (provide resources)
2. Find alternative approach
3. Simplify requirements
4. Get help from team/documentation
```

## 4️⃣ Implement Unblocking Actions

If blocker can be resolved now:

```bash
# Example: Create mock service
# Create mocks/auth-service.js
export const mockAuthService = {
  login: async (email, password) => {
    // Mock successful login
    return { token: 'mock-token', user: { email } };
  },
  logout: async () => true,
  validateToken: async () => true
};

# Update code to use mock in development
const authService = process.env.NODE_ENV === 'development' 
  ? mockAuthService 
  : realAuthService;
```

## 5️⃣ Update STATE.md

Move unblocked features to ready:

```markdown
## 📋 Ready to Start (Newly Unblocked)
### [Feature Name]
- **Was Blocked By**: [Previous blocker]
- **Unblocked Via**: [Resolution method]
- **Can Now Proceed**: With mock/workaround/partial implementation
- **Remember**: Update when real dependency available
```

## 6️⃣ Document Temporary Solutions

Create WORKAROUNDS.md if using mocks:

```markdown
# Temporary Workarounds

## Mock Authentication
- **File**: mocks/auth-service.js
- **Replace When**: Real auth service ready
- **Update Needed**: src/services/auth.js line 5
- **Tests to Update**: tests/integration/auth.test.js

## Hardcoded Config
- **File**: config/temp-config.js
- **Replace When**: Environment service ready
- **Values**: API_URL = "http://localhost:3000"
```

## 7️⃣ For Unresolvable Blockers

Document what's needed:

```markdown
## ⛔ Blockers Requiring External Action

### [Feature Name]
**Blocked By**: [Specific thing needed]
**Who Can Unblock**: [Person/team]
**Action Needed**: 
1. [Specific step 1]
2. [Specific step 2]
**Impact**: [What can't proceed]
**Workaround**: [None | Describe if exists]

### Request Template:
"Hi [Name], 
We need [specific thing] to proceed with [feature].
Could you please [specific action] by [date]?
This blocks [impact]."
```

## 8️⃣ Alternative Work Plan

If blockers can't be resolved:

```markdown
## 🔄 Alternative Work (While Blocked)

Instead of blocked features, work on:
1. **Documentation**: Update README, API docs
2. **Tests**: Increase coverage for completed features  
3. **Refactoring**: Improve code quality
4. **Performance**: Optimize existing features
5. **UI Polish**: Improve user experience
6. **Tech Debt**: Address TODOs and FIXMEs
```

## 9️⃣ Generate Blocker Report

```
📊 BLOCKER ANALYSIS REPORT
━━━━━━━━━━━━━━━━━━━━━━━
Total Blockers: X
Resolved This Session: Y
Remaining: Z

✅ Unblocked:
- [Feature]: Used mock service
- [Feature]: Created workaround

⚠️ Partially Unblocked:
- [Feature]: Can do 60% without dependency

❌ Still Blocked:
- [Feature]: Needs external API key
- [Feature]: Waiting for database team

💡 Recommendations:
1. Priority: Unblock [Feature] first (highest impact)
2. Request: Contact [person] for [resource]
3. Meanwhile: Work on [alternative tasks]

📈 Impact Analysis:
- Unblocking [Feature X] would enable Y other features
- Current velocity impact: -30% due to blockers
- Projected unblocked velocity: +50%
```

## 🎯 Next Actions
1. Implement identified workarounds
2. Send requests for external unblockers
3. Update STATE.md with newly ready work
4. Proceed with highest-priority unblocked feature
