---
name: vet-wf
description: Vet a Claude Code workflow (skills, agents, orchestrators) with two agents in parallel — a technical writer for documentation/logic quality and a code reviewer for implementation correctness. Use when you've just built or modified a skill, agent, or multi-agent pipeline and want a quality check before shipping.
allowed-tools: Task, Bash, Read, Glob, Grep
user-invocable: true
---

# Vet Workflow

Vet a Claude Code workflow (skills, agents, orchestrators) using two specialist agents in parallel. The technical writer checks SKILL.md files, agent definitions, output contracts, delegation instructions, and documentation for clarity, correctness, and completeness. The code reviewer checks Python scripts, shell commands, JSON schemas, and implementation logic for bugs and edge cases. Synthesize both perspectives into a filtered, actionable recommendation.

## Usage

```
/vet-wf
```

## Agent Selection

**Agent 1 — Documentation/workflow reviewer**: Prefer `arc-technical-writer`. If unavailable, use any technical writing, documentation, or general-purpose agent that can critically review skill SKILL.md files, agent definitions, and workflow logic.

**Agent 2 — Code reviewer**: Prefer `arc-code-reviewer`. If unavailable, use any code review agent that can check for bugs, logic errors, and edge cases. If no dedicated code review agent is available, use a general-purpose agent with explicit instructions to focus on implementation correctness.

If only one agent type is available, run that one and note which perspective is missing in the output.

## Process

### Step 1: Gather Context

Identify the workflow being vetted:
1. Check `git diff HEAD` and `git status` for recently changed files
2. Check `.todo.md` for current task context
3. Identify which skills, agents, scripts, and reference files are part of the active workflow
4. Note all relevant file paths — SKILL.md files, agent .md files, Python/shell scripts, output-format references

### Step 2: Run Both Agents in Parallel

Launch both agents simultaneously using the Task tool (single message, two Task calls).

**Agent 1 — Documentation/workflow reviewer**:
- Provide: list of all workflow files (SKILL.md, agent .md files, reference docs), task context, description of the workflow's intent
- Ask for: critical review of SKILL.md orchestration logic, agent output contracts, delegation instructions, output-format templates, and any documentation for clarity, correctness, and completeness
- Focus: are the instructions unambiguous? do the agents hand off correctly? are output contracts consistent? is anything misleading or missing?

**Agent 2 — Code reviewer**:
- Provide: list of all implementation files (Python scripts, shell commands in SKILL.md, JSON schemas)
- Ask for: code review for bugs, logic errors, edge cases, and anything that would break in real usage
- Focus: implementation correctness in scripts and structured data — not style nitpicks

### Step 3: Synthesize Findings

After both agents complete, compare and analyze their output:
- Look for overlapping concerns (higher signal — both agents flagging the same thing)
- Filter noise: discard style nitpicks, subjective preferences, over-engineering suggestions
- Identify genuine issues: bugs in scripts, broken delegation logic, misleading instructions, inconsistent output contracts
- Note useful-but-optional improvements separately

### Step 4: Present Recommendations

Output format:

```
## Workflow Vet Results

**Reviewed**: {brief description of what was reviewed}
**Agents**: {agent 1 name} + {agent 2 name}

### Recommended Changes
{Numbered list — real issues worth fixing, each with file:line reference and brief rationale}

### Optional Improvements
{Nice-to-haves, low priority}

### Dismissed
{What was filtered out and why, briefly}
```

## Important

- Run both agents **in parallel** (single message with two Task calls) — don't wait for one before launching the other
- Not every suggestion will be correct or worth making — apply judgment
- Don't implement changes — just recommend them and wait for user direction
- If nothing needs changing, say so clearly: "No changes recommended."
- Always end with: "Run `/vet-apply` to have me carefully implement the recommended changes."
