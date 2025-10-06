# CLAUDE.md - Universal Rules for CascadeProjects

## Core Principles
1. **Clarity Over Cleverness** - Write code that's immediately understandable
2. **Explicit Over Implicit** - State assumptions and decisions clearly
3. **Working Over Perfect** - Ship functional code, iterate based on feedback
4. **Context Preservation** - Always update context.md with significant changes

## Code Standards
- **Line Length**: 80 characters preferred, 100 maximum
- **Function Length**: 30 lines maximum, extract if larger
- **File Length**: 300 lines maximum, split if larger
- **Naming**: Descriptive names over abbreviations
- **Comments**: Explain "why" not "what"

## Communication Rules
- Start responses with current understanding
- Present multiple options with trade-offs
- Highlight assumptions being made
- Flag areas of uncertainty
- Connect technical choices to business value

## Development Process
1. **Understand** - Clarify requirements before coding
2. **Plan** - Outline approach before implementation
3. **Implement** - Build incrementally with tests
4. **Document** - Update context and decisions
5. **Validate** - Ensure success criteria are met

## Error Handling
- Fail fast with clear error messages
- Log errors with context
- Provide recovery suggestions
- Never silently fail

## Git Commits
Format: type(PROJECT-058-AnomalyInsights): description
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code improvement
- test: Test changes

## Terminal Environment Notes
**CRITICAL**: PowerShell Configuration Limitations
- `&&` operator not supported in this PowerShell version
- Use separate commands instead of chaining
- File redirection `<` not supported - use `Get-Content file | command` instead
- Escape sequences may fail - use Python wrapper for complex commands

Example workarounds:
```bash
# ❌ Don't use
command1 && command2
bq query < file.sql

# ✅ Use instead
command1
command2
Get-Content file.sql | bq query --use_legacy_sql=false
```

## Remember
- You're building production systems, not demos
- Every decision should trace to a requirement [R#]
- When uncertain, ask for clarification
- Preserve context for future sessions
