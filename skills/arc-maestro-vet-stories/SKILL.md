---
name: arc-maestro-vet-stories
description: "Audit a story backlog for quality and coherence. Evaluates each story individually and the collection as a whole -- completeness, clarity, assumptions, ordering, and gaps. Use when user says '/arc-maestro-vet-stories', 'vet the stories', 'audit the backlog', or 'check stories'."
allowed-tools: Read, Glob, Task, AskUserQuestion
user-invocable: true
argument-hint: "[path/to/stories]"
---

# Maestro Story Auditor

Quality gate for story backlogs. Runs a two-dimensional audit: individual story quality (element level) and cross-story coherence (collection level).

## When to Use

- Before handing stories to `/arc-maestro` for implementation
- After generating stories with `/arc-maestro-feature-planner` to verify quality
- To surface gaps, ordering problems, and contradictions across a backlog
- When reviewing or inheriting a set of stories someone else wrote

## Workflow

1. **Locate the backlog**
   - Default: `.stories/` in the current project directory
   - User can provide an alternate path: `/arc-maestro-vet-stories ./path/to/backlog`

2. **Delegate to the auditor agent**
   ```
   Task tool with subagent_type: ca-backlog-auditor
   ```

   Pass along:
   - Backlog directory path
   - Any project context or constraints the user has mentioned

3. **Present the audit results**
   - Element-level findings (per story)
   - Collection-level findings (cross-story)
   - Ask whether the user wants to address any reported issues

## What Gets Audited

### Element Level (Each Story)
- Clear rationale and user need
- Completion criteria that are specific and testable
- Positive, negative, and boundary cases addressed
- Reasonable scope (not too large or bundled)
- Assumptions stated and reasonable
- Unambiguous language throughout

### Collection Level (All Stories)
- Objective coverage: do stories collectively achieve the goal?
- Ordering: are dependencies identified and acyclic?
- Gaps: are connective or infrastructure stories missing?
- Contradictions: do any stories or criteria conflict?
- Sequencing: is the implementation order logical?
- Shared assumptions: do multiple stories rely on unverified premises?

## Examples

```
User: /arc-maestro-vet-stories
Claude: Auditing stories in .stories/ ...
[Spawns ca-backlog-auditor agent]
[Agent reads all stories, runs element + collection audit]
[Returns report with per-story findings and cross-story analysis]
```

With an explicit path:
```
User: /arc-maestro-vet-stories ./features/billing/stories
Claude: Auditing stories in ./features/billing/stories ...
```
