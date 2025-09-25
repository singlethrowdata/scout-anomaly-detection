Analyze project dependencies and update documentation.

## 1️⃣ Review All Features
Read CLAUDE.local.md and analyze each feature:

```markdown
Feature: [Name]
  What:
    - Requirement [R1] → needs: ? → provides: ?
    - Requirement [R2] → needs: ? → provides: ?
```

## 2️⃣ Build Dependency Graph
Create complete dependency map:

```
Foundation Layer (No dependencies):
├── Database → provides: data-storage
├── Config → provides: environment-settings
└── Logger → provides: logging

Service Layer (Needs foundation):
├── Auth → needs: data-storage → provides: user-context
├── Email → needs: config → provides: notifications
└── Cache → needs: config → provides: performance

Application Layer (Needs services):
├── API → needs: auth, data-storage → provides: endpoints
└── UI → needs: endpoints → provides: interface
```

## 3️⃣ Check for Issues

### Circular Dependencies:
- A needs B, B needs C, C needs A? ❌
- Flag any circular references found

### Missing Dependencies:
- Feature references capability not provided by any feature
- Flag as "External dependency" or "Missing feature"

### Over-Constraints:
- Features that could be parallelized but marked sequential
- Suggest dependency refinement

## 4️⃣ Identify Parallel Opportunities
Find features that can be built simultaneously:

```markdown
## Parallel Work Opportunities

After Database is complete, these can be done in parallel:
- Team 1: Authentication (provides: user-context)
- Team 2: Email Service (provides: notifications)
- Team 3: Cache Layer (provides: performance)

These features don't conflict because:
- Different files/modules
- No shared dependencies
- Independent test suites
```

## 5️⃣ Update STATE.md
Revise based on dependency analysis:

```markdown
## 📋 Ready to Start (Unblocked)
[List all features whose dependencies are now met]

## ⛔ Blocked Features
[Update with correct blockers]

## 🔥 Critical Path
[Show the must-do-first sequence]
```

## 6️⃣ Generate Optimal Build Sequence

```markdown
## Recommended Implementation Order

Phase 1: Foundation (No dependencies)
- [ ] Database (2 hours)
- [ ] Configuration (1 hour)
Can be parallelized

Phase 2: Core Services (After Phase 1)
- [ ] Authentication (3 hours) 
- [ ] Email Service (2 hours)
Can be parallelized

Phase 3: Integration (After Phase 2)
- [ ] API Endpoints (4 hours) - Needs auth
- [ ] Admin Panel (3 hours) - Needs auth
Can be parallelized

Phase 4: UI (After Phase 3)
- [ ] Frontend (6 hours) - Needs API

Total: ~21 hours sequential
With parallelization: ~13 hours
Time saved: 8 hours (38%)
```

## 7️⃣ Update CLAUDE.local.md
If dependencies are wrong/missing, update:

```markdown
Feature: [Name] {
  What:
    - "Requirement" [R1]
      → needs: [correct-dependency]
      → provides: [correct-capability]
}
```

## 8️⃣ Create Dependency Report

```
📊 DEPENDENCY ANALYSIS
━━━━━━━━━━━━━━━━━━━━
Total Features: X
Independent: Y (can start immediately)
Dependent: Z (need other features first)

✅ No Issues Found | ⚠️ Issues Found:
- [List any circular dependencies]
- [List any missing dependencies]

🔄 Parallel Opportunities:
- Phase 1: X features (Y hours saved)
- Phase 2: X features (Y hours saved)

📈 Efficiency Gain:
- Sequential time: X hours
- Parallel time: Y hours
- Time saved: Z hours (N%)

🎯 Recommendation:
[Specific next steps based on analysis]
```

## 9️⃣ Save Analysis
Update project documentation:
- Dependency graph → ARCHITECTURE.md
- Build sequence → STATE.md
- Issues found → CLAUDE.local.md notes
