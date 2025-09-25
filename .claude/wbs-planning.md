# WBS Planning Guide for PROJECT-058-AnomalyInsights

## Opening Script for Claude Code

"Welcome to PROJECT-058-AnomalyInsights planning. I'll guide you through defining the Place-Making atmosphere and What-Boundaries-Success framework for this project.

**Project Purpose**: Automated GA4 anomaly detection system with ML insights for 50+ STM clients
**Project Type**: data-pipeline

Let's start by defining what kind of PLACE this will be, then specify requirements."

## 0. PLACE-MAKING - Atmosphere Definition (ASK FIRST)

Before any technical planning:
1. **Physical Metaphor**: "If this software was a physical place, what would it be?"
   - Don't say "an app" or "a tool" - think physical spaces
   - Is it a factory? A river? A refinery?

2. **Signature Element**: "What's the ONE unique thing users will remember?"
   - Visual texture? Interaction pattern? Sound? Motion?
   - This must appear everywhere in the product

3. **Transformation**: "Who does someone become after using this?"
   - They arrive as [current state]
   - They leave as [transformed state]
   - The product enabled [new capability/perspective]

4. **Beneficial Friction**: "Where should we intentionally slow things down?"
   - What deserves attention?
   - What needs careful thought?
   - Where does speed hurt the experience?

5. **Anti-Atmosphere**: "What should this place NEVER feel like?"
   - Wrong metaphors to avoid
   - Feelings to prevent
   - Optimizations that would ruin it

## 1. WHAT - Requirements Gathering

Ask these questions:
- What specific problems does this solve?
- What are the core features (list each)?
- What actions will users take?
- What data inputs are expected?
- What outputs must be produced?
- Are there any compliance requirements?

Tag each requirement: [R1], [R2], etc.

## 2. BOUNDARIES - Constraints Definition

Explore these constraints:
- **Performance**: Response time? Concurrent users? Data volume?
- **Technology**: Required stack? Must-have integrations?
- **Resources**: Timeline? Budget? Team size?
- **Security**: Authentication needs? Data privacy requirements?
- **Scalability**: Current load? Future growth expectations?
- **Compatibility**: Browser support? Device requirements?

Each boundary should eliminate specific invalid solutions.

## 3. SUCCESS - Measurable Criteria

Define success metrics:
- How do we know each requirement is complete?
- What performance benchmarks must be met?
- What quality standards apply?
- What tests must pass?
- What user feedback indicates success?
- Are there business metrics to track?

## 4. ANTI-REQUIREMENTS - What NOT to Build

Clarify scope:
- What features are explicitly OUT of scope?
- What complexity should we avoid?
- What integrations are NOT needed?
- What scale are we NOT targeting yet?

## 5. SOLUTION SPACE ANALYSIS

After gathering above:
- Initial solution space: ~[X] possible approaches
- After boundaries: Reduced to ~[Y] valid solutions
- Recommended approach: [Describe]
- Trade-offs: [List key decisions]

## Output Format

Update CLAUDE.local.md with:
1. Complete Place-Making Specification section
2. Atmosphere Requirements [AR1-AR5]
3. Structured WBS with atmosphere annotations:
   - Group related requirements into Features
   - Each Feature has What/Boundaries/Success
   - Include atmosphere notes for each feature
   - Show how features support the metaphor
4. Solution space reduction metrics
5. Implementation order considering atmosphere
