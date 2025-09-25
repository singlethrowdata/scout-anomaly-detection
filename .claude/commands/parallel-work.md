Identify opportunities for parallel development and set up git worktrees.

## 1️⃣ Analyze Current State
Read STATE.md and identify:
- All completed features and what they provide
- All features with satisfied dependencies
- Features that don't conflict (different modules/files)

## 2️⃣ Find Parallelizable Work

```markdown
## Features Ready for Parallel Development

Based on completed dependencies:

Track 1: Authentication Module
- Feature: UserAuth
- Files: src/auth/*, tests/auth/*
- No conflicts with other tracks
- Estimated: 3 hours

Track 2: Email Service  
- Feature: EmailNotifications
- Files: src/email/*, tests/email/*
- No conflicts with other tracks
- Estimated: 2 hours

Track 3: Cache Layer
- Feature: RedisCache
- Files: src/cache/*, tests/cache/*
- No conflicts with other tracks
- Estimated: 2 hours

These can be developed simultaneously because:
✅ All dependencies satisfied
✅ Different code modules
✅ Independent test suites
✅ No shared state
```

## 3️⃣ Set Up Git Worktrees

Generate commands for parallel setup:

```bash
# Navigate to parent directory
cd ..

# Create worktree for each parallel track
git worktree add -b feature/auth ./project-auth
git worktree add -b feature/email ./project-email  
git worktree add -b feature/cache ./project-cache

# Each worktree has its own working directory
# Team members (or Claude instances) can work independently
```

## 4️⃣ Create Work Assignments

```markdown
## Parallel Work Assignment

### Track 1: Authentication (./project-auth)
Developer/Claude Instance: #1
```bash
cd ../project-auth
claude chat
```
Instructions:
1. Implement UserAuth feature
2. Follow TDD process
3. Update STATE.md in this worktree
4. Commit to feature/auth branch

### Track 2: Email Service (./project-email)
Developer/Claude Instance: #2
```bash
cd ../project-email
claude chat
```
Instructions:
1. Implement EmailNotifications
2. Follow TDD process
3. Update STATE.md in this worktree
4. Commit to feature/email branch

### Track 3: Cache Layer (./project-cache)
Developer/Claude Instance: #3
```bash
cd ../project-cache
claude chat
```
Instructions:
1. Implement RedisCache
2. Follow TDD process
3. Update STATE.md in this worktree
4. Commit to feature/cache branch
```

## 5️⃣ Integration Points

Identify where parallel work must merge:

```markdown
## Integration Schedule

Phase 1 (Parallel): 0-3 hours
- All three tracks work independently
- No synchronization needed

Phase 2 (Integration): 3-4 hours
- Merge feature/auth to main
- Merge feature/email to main
- Merge feature/cache to main
- Resolve any conflicts (unlikely if modules are separate)

Phase 3 (Dependent Features): 4+ hours
- API Endpoints (needs auth merged)
- Admin Panel (needs auth merged)
- These can now start
```

## 6️⃣ Monitoring Script

Create a monitoring script to check progress:

```bash
#!/bin/bash
# check-parallel-progress.sh

echo "🔄 Parallel Development Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for worktree in project-auth project-email project-cache; do
  echo "\n📁 $worktree:"
  cd ../$worktree
  git status --short
  echo "Last commit: $(git log -1 --oneline)"
done

echo "\n📊 Test Status:"
npm test 2>/dev/null | grep -E "(passing|failing)"
```

## 7️⃣ Calculate Time Savings

```markdown
## Efficiency Analysis

Sequential Development:
- Auth: 3 hours
- Email: 2 hours  
- Cache: 2 hours
- Total: 7 hours

Parallel Development:
- All three simultaneously: 3 hours (longest task)
- Integration: 1 hour
- Total: 4 hours

Time Saved: 3 hours (43% reduction)
```

## 8️⃣ Generate Parallel Plan

```
📊 PARALLEL DEVELOPMENT PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━
Parallel Tracks: 3
Time Saving: 43% (3 hours)
Complexity: Low (independent modules)

✅ Ready to Execute:
1. Run worktree setup commands
2. Start 3 Claude instances (or assign to team)
3. Each track follows TDD independently
4. Merge when all complete

⚠️ Watch For:
- Shared utility functions (coordinate if needed)
- Database migrations (apply in order)
- Config file changes (may need manual merge)

🎯 Go/No-Go Decision:
[✅ GO - High confidence in parallel execution]
[⚠️ WAIT - Need to resolve: (list issues)]
```

## 9️⃣ Cleanup Commands

After integration:
```bash
# Remove worktrees when done
git worktree remove ../project-auth
git worktree remove ../project-email  
git worktree remove ../project-cache

# Delete merged branches
git branch -d feature/auth feature/email feature/cache
```

Parallel development plan is ready for execution!
