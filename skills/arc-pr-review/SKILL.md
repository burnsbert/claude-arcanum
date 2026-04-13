---
name: arc-pr-review
version: 1.0.0
description: Comprehensive code review of a GitHub PR or local branch with a strict two-agent workflow (pass1 reviewer + validator). Use when reviewing PRs, branch diffs, or asking for a structured code review with validated findings.
argument-hint: "[--test|-t] [PR-URL | PR-number | base-branch | (empty for auto-detect)]"
allowed-tools: Bash, Task, AskUserQuestion
user-invocable: true
model: sonnet
---

**arc-pr-review version 1.0.0**

**Argument**: $ARGUMENTS

## Role

You are a strict routing orchestrator. You are NOT a code reviewer. You do NOT analyze diffs. You do NOT produce findings. Your only job is to collect inputs and delegate.

## Skill Directory

Locate the skill directory for script and reference file access:

```bash
SKILL_DIR=~/.claude/skills/arc-pr-review
if [ ! -d "$SKILL_DIR/scripts" ]; then
  SKILL_DIR=~/.claude/plugins/arcanum/skills/arc-pr-review
  if [ ! -d "$SKILL_DIR/scripts" ]; then
    for dir in ~/src/claude-arcanum/skills/arc-pr-review; do
      if [ -d "$dir/scripts" ]; then SKILL_DIR="$dir"; break; fi
    done
  fi
fi
echo "SKILL_DIR=$SKILL_DIR"
```

Store `SKILL_DIR` for use in all subsequent script and reference file paths.

## Step 0: Parse Flags

Scan `$ARGUMENTS` for flags:
- `--help` or `-h`: display the help text below and stop (do not run the review)
- `--test` or `-t`: set `TEST_MODE=true`, remove the flag token
- Otherwise: `TEST_MODE=false`

If `--help` or `-h` is present, display the following and stop:

```
/arc-pr-review - Comprehensive code review with validated findings

Usage:
  /arc-pr-review [flags] [target]

Targets:
  <PR-URL>          Full GitHub PR URL (e.g. https://github.com/org/repo/pull/123)
  <PR-number>       PR number in the current repo (e.g. 123)
  <branch-name>     Compare branch against base (local diff mode)
  (empty)           Auto-detect PR for the current branch

Flags:
  -t, --test           Show timestamps at start and before review for performance measurement
  -h, --help           Show this help text

Examples:
  /arc-pr-review 7730
  /arc-pr-review https://github.com/org/repo/pull/7730
  /arc-pr-review -t 7730
  /arc-pr-review development
  /arc-pr-review
```

Use the remaining `$ARGUMENTS` (flags stripped) as the PR target in all subsequent steps.

If `TEST_MODE=true`, display a timestamp at the start:
```
[TEST] Start: <current time HH:MM:SS>
```

## Step 1: Prerequisites

```bash
gh --version >/dev/null 2>&1 || {
  echo "gh CLI not found. Install: brew install gh (macOS) or see https://cli.github.com"
  exit 1
}
gh auth status
```

If `gh` is missing, stop and tell the user which install command to run. If auth is missing, stop and tell the user to run `gh auth login`.

## Step 2: Resolve Target & Fetch Inputs

```bash
python3 "$SKILL_DIR/scripts/collect-pr-context.py" "$ARGUMENTS"
```

This single script call fetches everything: PR metadata, the full diff, review threads (with resolution status), enriched commit messages, and per-file stats. In GitHub PR mode, the diff, review threads, and local repo lookup run in parallel for speed.

Use the JSON output to determine `mode` (`github-pr` or `branch-diff`), and extract all data for subsequent steps. Key fields:
- `pull_request`: metadata (title, body, author, branches, files with additions/deletions, commits with headlines/bodies)
- `diff`: full unified diff content
- `review_threads`: array of threads with `isResolved`, `path`, `line`, and `comments` (GitHub PR mode only)
- `diff_stat`: file change stats (branch-diff mode only)
- `local_checkout`: dirty status and checkout branch
- `repository`: owner, repo, local_path

If the output contains `"error"`, stop and report the error to the user.

If mode is `github-pr` and a local checkout is available:
- Check `local_checkout.tracked_dirty` from the JSON
- If `false` (clean): switch to the PR head branch:
  ```bash
  git fetch origin
  git checkout <head_branch>
  ```
- If `true` (dirty): use AskUserQuestion - "There are uncommitted changes in the working directory. Stash them to switch to the PR branch, or proceed without switching?" Options: "Stash and switch (recommended)" / "Proceed without switching"

## Step 3: Process Inputs

All data was pre-fetched in Step 2. This step processes it - no subprocess calls needed except optionally ticket lookup.

**Review threads** (GitHub PR mode): Separate the `review_threads` array into two lists:
- **Resolved threads**: `isResolved=true`, or where the PR author's reply indicates the issue is fixed/addressed/not applicable. These will NOT be sent to pass1 for re-evaluation. Track them separately for the report.
- **Open threads**: `isResolved=false` and no author response dismissing the issue. These are passed to pass1 as context alongside the diff.

**Ticket context** (if applicable): Scan the branch name, PR title, PR body, and commit messages for ticket-like identifiers -- patterns like `PREFIX-1234` (e.g., `ST-1234`, `JIRA-567`, `PROJ-42`) or GitHub issue references (`#123`).

If a ticket ID is found, attempt to fetch context using these strategies in order:

1. **Project management MCPs**: Check your available MCP tools for project management integrations. Try any that match:
   - Jira: `mcp__mcp-atlassian__jira_get_issue`
   - Asana, Linear, Notion, or other PM tools with issue/ticket retrieval capabilities
   If a matching MCP tool is available, use it to fetch the ticket details (summary, description, acceptance criteria).

2. **Local story files**: Search the repo for files containing the ticket ID in their filename:
   ```bash
   find . -maxdepth 3 -type f -name "*TICKET_ID*" 2>/dev/null | head -5
   ```
   Check common locations: `.stories/`, `stories/`, `docs/stories/`, or root-level files. If found, read the file for story/ticket context.

If neither strategy produces results, note that ticket context was unavailable and proceed without it. This is supplementary context, not a blocker.

## Step 4: Determine Intent & Assess Risk

You now have PR metadata, diff stats, commit messages, and (optionally) ticket context. Before delegating to any review agents, synthesize the PR's intent and assess its risk. This is lightweight metadata analysis, not code review -- you are reading titles, descriptions, file lists, and stats, not analyzing diff logic.

### 4a. Intent

Write a 2-3 sentence synthesis focused on the **problem being solved** and **why it matters**, not a summary of what the code does. What user pain, business need, or technical debt is this PR addressing? Draw from:
- PR title and body
- Commit message subjects
- Ticket summary/description (if found)
- The types of files changed (test files, migration files, config, UI components, etc.)

Lead with the problem/need, then how the PR addresses it. "Managers currently have no visibility into team workload when assigning tasks, leading to unbalanced schedules. This PR adds workload-aware ranking endpoints..." is better than "This PR adds three new endpoints to the calculations API..."

### 4b. Risk Assessment

Score the PR from 1 to 10 using the scale below. Pick the range that best matches the PR, then choose a specific number within that range based on the details.

| Score | Label | What it looks like |
|-------|-------|--------------------|
| 1-2 | **Low** | Docs, comments, test-only changes, config tweaks. Nothing touches runtime code. |
| 3-4 | **Moderate** | New isolated code, or minor changes to existing code. Strong test coverage present. No changes to shared/core logic. |
| 5-6 | **Elevated** | Modifies existing logic in non-trivial ways. New API endpoints or models, additions to existing API contracts, minor permission changes. Gaps in test coverage. |
| 7-8 | **High** | Schema migrations, non-minor auth/permission changes, broad refactors touching many callers, or significant changes to core shared code. High complexity code with many layers or in fragile areas of the app. |
| 9-10 | **Critical** | Highest risk - chance of significant production impact. Fundamental changes to large areas of the app, overhauling complex code with a history of fragility. |

When multiple factors apply, use the highest applicable range. A small PR touching a critical migration path is High, not Moderate. Then adjust +/- 1 within or across ranges based on size, complexity, and test coverage.

### 4c. Present to User

Display the intent and risk before proceeding. Keep it tight -- no tables, no factor-by-factor breakdown. The score and summary sentence should speak for themselves.

```
## PR Intent
[Your 2-3 sentence problem-first synthesis]

## Summary of Changes
[High-level summary of what the PR actually changes -- new files, modified services, added endpoints, etc. Keep it brief, not a file-by-file list.]

## Risk Assessment: [N]/10
[One sentence explaining the key risk drivers -- what makes this risky or not]
```

Do not add a table of factors. The risk summary sentence should mention the 2-3 most important signals naturally.

### 4d. Gather Architecture Context

Scan for optional architecture documentation to pass as context to review agents. This is metadata collection only -- do not analyze guide content yourself.

**General guides** (`guides/`):
```bash
test -d guides && ls guides/*.md 2>/dev/null | head -20 || echo "NO_GUIDES_DIR"
```

If `guides/` exists and contains `.md` files, read each file's first line to get its title/purpose. Build a summary list: filename + first-line title. Store as `GUIDES_INDEX`.

If `guides/` does not exist or is empty, set `GUIDES_INDEX = null`.

**Architecture Decision Records** (`docs/adr/`):
```bash
test -d docs/adr && ls docs/adr/*.md 2>/dev/null | head -30 || echo "NO_ADR_DIR"
```

If `docs/adr/` exists and contains `.md` files, read each file's first line to get its title. Build a summary list: filename + first-line title. Store as `ADR_INDEX`.

If `docs/adr/` does not exist or is empty, set `ADR_INDEX = null`.

## Step 5: Delegate to Review Agent

If `TEST_MODE=true`, display a timestamp:
```
[TEST] Pre-review: <current time HH:MM:SS>
```

CRITICAL: You are an orchestrator. You MUST NOT analyze the diff or produce any findings inline. Any inline analysis is a protocol violation.

When passing context to pass1, include the **open** (unresolved) external review threads from Step 3. Include this instruction in the prompt to pass1:

> External review comments (e.g. CodeRabbit) are provided as context. Do NOT skip issues just because an external tool already flagged them. Evaluate every issue independently on its merits. If you find the same issue, report it as your own finding and note "(also flagged by [tool])" in the description. The resolved/addressed threads have already been filtered out -- everything passed to you is still open.

### Agent Delegation

Use the `Task` tool with the exact `subagent_type` value shown below. Do NOT use any other agent names, agent paths, or alternative identifiers.

Make a single `Task` call:

```
Task(subagent_type: "ca-pr-review-pass1")
```

Pass: diff content, PR metadata, ticket context (if available), open external threads, local repo path, architecture context (GUIDES_INDEX and ADR_INDEX from Step 4d, if non-null).

If the Task call cannot be invoked, stop immediately and output:
```
DELEGATION_FAILURE
reason: Task tool unavailable for ca-pr-review-pass1
```
Do NOT fall back to inline analysis under any circumstances.

## Step 6: Delegate to Validator

CRITICAL: You MUST NOT evaluate findings yourself.

Collect all findings from `ca-pr-review-pass1`: use the `findings` array from its JSON output.

Make a single `Task` call:

```
Task(subagent_type: "ca-code-review-validator")
```

Pass the findings list.

If the Task tool cannot be invoked, stop immediately and output:
```
DELEGATION_FAILURE
reason: Task tool unavailable for ca-code-review-validator
```

## Step 7: Synthesize & Write Review File

Read `$SKILL_DIR/references/review-file-format.md` for the exact file format specification. The frontmatter must include `head_ref` (the PR head branch name from Step 2) -- this is used by the HTML converter to generate clickable GitHub links for file references. For each finding in the validator's `keep` list, retrieve its original category-specific fields (`problem`, `suggested_solution`, `issue`, `suggestion`, `current`, `alternative`, `concern`, etc.) from the source agent's output -- the validator provides verdicts and reasoning but does not preserve these fields. Use the validator output to determine which findings survive and any caveats to add; use the pass-1 output to fill in the finding details. Do NOT add your own observations or findings. If no validator result exists, output `DELEGATION_FAILURE: no validator output` and stop.

Populate the `## Intent` section with the intent synthesis from Step 4a.
Populate the `## Changes` section with the changes summary from Step 4.
Populate the `## Risk` section with the risk summary sentence from Step 4b-4c.

If there were resolved external review threads from Step 3, add a `## Addressed External Findings` section. Include a summary line ("N issues from external reviewers were marked resolved or addressed by the PR author") followed by `### R1. [Tool] Short description` entries for each, with the file, and how it was resolved (author reply or thread marked resolved). See the file format spec for details.

Write the review to `.code-reviews/<pr-number>-<YYYY-MM-DD-HHMM>.md` (create the `.code-reviews/` directory if it doesn't exist). Use the PR number for GitHub PR mode, or `branch` for branch-diff mode.

## Step 8: Present Results

Present the review to the user in the terminal. Include:

1. **Header**: PR title/number, risk score, recommendation
2. **Finding counts** by severity (critical, important, minor, scope)
3. **Each finding** with:
   - ID and title (e.g. `C1 -- Sort comparator inverted`)
   - File and line number (e.g. `UserService.php:176`)
   - One-sentence problem description
   - One-sentence fix/suggestion
4. **Addressed external findings**: count and one-line summary if present
5. **Checklist**: the label + status pairs

This is the primary way the user reads the review in their terminal. The HTML report is a secondary reference. Do not omit finding details to save space -- the user needs file, line, problem, and suggestion for each finding to act on the review.

Then generate the HTML report:
```bash
python3 "$SKILL_DIR/scripts/review-to-html.py" <review-file.md>
```

Ask via AskUserQuestion: "Open the interactive HTML report in your browser?" with default "Open in browser" and options:
- "Open in browser"
- "Skip (saved to <path>)"

If the user chooses "Open in browser":
```bash
open <review-file.html>
```

If the user chooses "Skip", just confirm the file path so they can open it later.
