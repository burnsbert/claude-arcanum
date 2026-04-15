---
name: vet
description: Review recent work with an agent, vet feedback, and recommend worthwhile changes
allowed-tools: Task, Bash, Read, Glob, Grep, TodoWrite
user-invocable: true
---

# Vet Recent Work

Review what was just done using a specialized agent, vet the feedback to filter noise, and recommend changes worth making.

## Usage

```
/vet [agent-name]
```

- **With agent**: `/vet arc-technical-writer` - use specified agent
- **Without agent**: `/vet` - auto-select based on context

## Agent Selection Logic

When no agent specified, analyze recent work to choose:

| Recent Work Type | Default Agent |
|-----------------|---------------|
| Claude agents/skills/prompts | `arc-technical-writer` |
| Code changes (features, fixes) | `arc-code-reviewer` |
| Test code | `arc-code-reviewer` |
| Documentation (non-agent .md) | `arc-technical-writer` |

If the preferred agent is not available, pick the best suitable alternative from whatever agents are installed. For code/test work, any code review agent works. For agents/skills/docs, any technical writing or general-purpose agent works. If truly nothing suitable is available, use the general-purpose agent.

## Process

### Step 1: Determine Context

Check what was recently worked on:
1. Look at `git diff HEAD` and `git status` for recent changes
2. Check `.todo.md` for current task context
3. Identify file types and domains affected

### Step 2: Select Agent

If user specified an agent, use it. Otherwise:
1. Analyze the file types in recent changes
2. Match to the appropriate agent from the table above
3. Announce: "Using **{agent-name}** to review {description of work}"

### Step 3: Run Review

Launch the selected agent with Task tool:
- Provide context about what was just done
- Ask for critical feedback, not nitpicks
- Request specific, actionable findings

### Step 4: Vet Feedback

Filter the agent's feedback:
- **Keep**: Real bugs, security issues, logic errors, significant improvements
- **Discard**: Style nitpicks, subjective preferences, over-engineering suggestions
- **Flag as optional**: Nice-to-haves that don't block

### Step 5: Present Recommendations

Format output as:

```
## Review Summary

**Agent**: {agent-name}
**Reviewed**: {brief description of what was reviewed}

### Recommended Changes
{Numbered list of changes worth making, each with file:line reference and brief rationale}

### Optional Improvements
{Nice-to-haves that could be skipped}

### Dismissed Feedback
{Brief note on what was filtered out and why}
```

## Important

- Be concise in recommendations - user wants quick decisions
- If no changes needed, say so clearly: "No changes recommended. Work looks solid."
- Don't implement changes - just recommend them and wait for user direction
- Always end with: "Run `/vet-apply` to have me carefully implement the recommended changes."
