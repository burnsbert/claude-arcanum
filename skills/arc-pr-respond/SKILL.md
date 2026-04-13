---
name: arc-pr-respond
version: 1.0.0
description: Analyze feedback on your GitHub pull request, validate each actionable item, and produce a prioritized analysis with recommended actions and an interactive HTML report. For PR authors responding to reviewers.
argument-hint: "[--test|-t] [--help|-h] <PR-URL | PR-number> [humans | reviewer-names... | --reviewers=name,name]"
allowed-tools: Bash, Task, AskUserQuestion
user-invocable: true
model: sonnet
---

**arc-pr-respond version 1.0.0**

**Argument**: $ARGUMENTS

## Role

You are a strict routing orchestrator. You are NOT a feedback analyst. You do NOT evaluate review comments. You do NOT produce action items. Your only job is to collect inputs and delegate.

## Skill Directory

Locate the skill directory for script and reference file access:

```bash
SKILL_DIR=~/.claude/skills/arc-pr-respond
if [ ! -d "$SKILL_DIR/scripts" ]; then
  SKILL_DIR=~/.claude/plugins/arcanum/skills/arc-pr-respond
  if [ ! -d "$SKILL_DIR/scripts" ]; then
    for dir in ~/src/claude-arcanum/skills/arc-pr-respond; do
      if [ -d "$dir/scripts" ]; then SKILL_DIR="$dir"; break; fi
    done
  fi
fi
echo "SKILL_DIR=$SKILL_DIR"
```

Store `SKILL_DIR` for use in all subsequent script and reference file paths.

## Step 0: Parse Flags

Scan `$ARGUMENTS` for flags:
- `--help` or `-h`: display the help text below and stop (do not run the analysis)
- `--test` or `-t`: set `TEST_MODE=true`, remove the flag token
- Otherwise: `TEST_MODE=false`

If `--help` or `-h` is present, display the following and stop:

```
/arc-pr-respond - Analyze PR feedback with validated findings and recommended actions

Usage:
  /arc-pr-respond [flags] <target> [filters]

Targets:
  <PR-URL>          Full GitHub PR URL (e.g. https://github.com/org/repo/pull/123)
  <PR-number>       PR number in the current repo (e.g. 123)

Filters:
  humans                          Exclude bot feedback
  <reviewer-name>                 Only feedback from specific reviewer(s)
  --reviewers=name1,name2         Comma-separated reviewer filter

Flags:
  -t, --test           Show timestamps at start and before analysis for performance measurement
  -h, --help           Show this help text

Examples:
  /arc-pr-respond 7730
  /arc-pr-respond https://github.com/org/repo/pull/7730
  /arc-pr-respond 7730 humans
  /arc-pr-respond 7730 brian
  /arc-pr-respond --reviewers=brian,sarah 7730
  /arc-pr-respond -t 7730
  /arc-pr-respond -h
```

Use the remaining `$ARGUMENTS` (flags stripped) as the target in all subsequent steps.

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

## Step 2: Fetch Feedback

```bash
mkdir -p .code-reviews
python3 "$SKILL_DIR/scripts/fetch-feedback.py" $ARGUMENTS | tee .code-reviews/.fetch-pending.json
```

This single script call fetches everything: PR metadata, the full diff, review threads (with resolution status), enriched commit messages, per-file stats, inline comments, issue comments, and local repo info. Diff, review threads, inline comments, issue comments, and local repo lookup run in parallel for speed.

The output is immediately saved to `.code-reviews/.fetch-pending.json` via `tee` -- this file becomes the `.feedback.json` sidecar in Step 7. Never reproduce this JSON by hand; always copy the file.

Use the JSON output to extract all data for subsequent steps. Key fields:
- `pull_request`: metadata -- `title`, `body`, `author`, `head_branch` (PR branch name), `base_branch`, `files` (array of `{path, additions, deletions}`), `files_changed` (count), `commits` (array with `headline`, `body`)
- `diff`: full unified diff content
- `review_threads`: array of threads with `isResolved`, `path`, `line`, and `comments`
- `items`: normalized feedback items with reviewer info and display names
- `counts`: total items, per-reviewer counts, per-source counts
- `local_repo_path`: path to local checkout (if found)
- `local_checkout`: dirty status and checkout branch

If the output contains `"error"`, stop and report the error to the user.

If `counts.total_items` is 0, stop and tell the user there is no review feedback to analyze.

If a local repo path is available:
- Check `local_checkout.tracked_dirty` from the JSON
- If `false` (clean): switch to the PR head branch:
  ```bash
  git fetch origin
  git checkout <head_branch>
  ```
- If `true` (dirty): use AskUserQuestion - "There are uncommitted changes in the working directory. Stash them to switch to the PR branch, or proceed without switching?" Options: "Stash and switch (recommended)" / "Proceed without switching"

## Step 3: Process Inputs

All data was pre-fetched in Step 2. This step processes it - no subprocess calls needed except optionally ticket lookup.

**Review threads**: Separate the `review_threads` array into two lists:
- **Resolved threads** (`isResolved=true`): These become the "Handled Feedback" section in the report. NOT sent to pass1 for re-evaluation. Track them separately.
- **Open threads** (`isResolved=false`): Passed to pass1 as context alongside the normalized feedback items.

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

You now have PR metadata, diff stats, commit messages, and (optionally) ticket context. Before delegating to any analysis agents, synthesize the PR's intent and assess its risk. This is lightweight metadata analysis, not feedback evaluation - you are reading titles, descriptions, file lists, and stats, not analyzing diff logic.

### 4a. Intent

Write a 2-3 sentence synthesis focused on the **problem being solved** and **why it matters**, not a summary of what the code does. What user pain, business need, or technical debt is this PR addressing? Draw from:
- PR title and body
- Commit message subjects
- Ticket summary/description (if found)
- The types of files changed (test files, migration files, config, UI components, etc.)

Lead with the problem/need, then how the PR addresses it.

### 4b. Risk Assessment

Score the PR from 1 to 10 using the scale below. Pick the range that best matches the PR, then choose a specific number within that range based on the details.

| Score | Label | What it looks like |
|-------|-------|--------------------|
| 1-2 | **Low** | Docs, comments, test-only changes, config tweaks. Nothing touches runtime code. |
| 3-4 | **Moderate** | New isolated code, or minor changes to existing code. Strong test coverage present. No changes to shared/core logic. |
| 5-6 | **Elevated** | Modifies existing logic in non-trivial ways. New API endpoints or models, additions to existing API contracts, minor permission changes. Gaps in test coverage. |
| 7-8 | **High** | Schema migrations, non-minor auth/permission changes, broad refactors touching many callers, or significant changes to core shared code. High complexity code with many layers or in fragile areas of the app. |
| 9-10 | **Critical** | Highest risk - chance of significant production impact. Fundamental changes to large areas of the app, overhauling complex code with a history of fragility. |

When multiple factors apply, use the highest applicable range.

### 4c. Present to User

Display the intent and risk before proceeding. Keep it tight - no tables, no factor-by-factor breakdown.

```
## PR Intent
[Your 2-3 sentence problem-first synthesis]

## Summary of Changes
[High-level summary of what the PR actually changes]

## Risk Assessment: [N]/10
[One sentence explaining the key risk drivers]
```

### 4d. Gather Architecture Context

Scan for optional architecture documentation to pass as context to analysis agents. This is metadata collection only -- do not analyze guide content yourself.

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

## Step 5: Delegate to Analysis Agent

If `TEST_MODE=true`, display a timestamp:
```
[TEST] Pre-analysis: <current time HH:MM:SS>
```

CRITICAL: You are an orchestrator. You MUST NOT analyze the feedback or produce any findings inline. Any inline analysis is a protocol violation.

When passing context to pass1, include the **open** (unresolved) review threads from Step 3 and the full diff from Step 2. Include this instruction in the prompt to pass1:

> Open review thread comments are provided as context alongside the normalized feedback items. Use the diff to understand the code context when classifying feedback severity and drafting responses. The resolved/handled threads have already been filtered out - everything passed to you is still open.

### Agent Delegation

Use the `Task` tool with the exact `subagent_type` value shown below. Do NOT use any other agent names, agent paths, or alternative identifiers.

Make a single `Task` call:

```
Task(subagent_type: "ca-pr-respond-pass1")
```

Pass: normalized feedback items, PR metadata, diff content, open review threads, local repo path, architecture context (GUIDES_INDEX and ADR_INDEX from Step 4d, if non-null).

If the Task call cannot be invoked, stop immediately and output:
```
DELEGATION_FAILURE
reason: Task tool unavailable for ca-pr-respond-pass1
```
Do NOT fall back to inline analysis under any circumstances.

## Step 6: Delegate to Validator

CRITICAL: You MUST NOT evaluate findings yourself.

Collect actionable findings into a single batch (do NOT include question_items or praise_items -- handle those directly in Step 7):
- All findings from `ca-pr-respond-pass1`: use the `items` array from its JSON output

Make a single `Task` call:

```
Task(subagent_type: "ca-code-review-validator")
```

Pass the items list.

If the Task tool cannot be invoked, stop immediately and output:
```
DELEGATION_FAILURE
reason: Task tool unavailable for ca-code-review-validator
```

## Step 7: Synthesize & Write Respond File

Read `$SKILL_DIR/references/respond-file-format.md` for the exact file format specification. The frontmatter must include `head_ref` set to `pull_request.head_branch` from the Step 2 JSON -- this is used by the HTML converter to generate clickable GitHub links for file references.

**IMPORTANT**: Unlike arc-pr-review, the arc-pr-respond workflow does NOT discard invalid reviewer feedback. Every reviewer comment appears in the report. The validator's verdicts determine severity classification, not inclusion.

- Validator `keep` items: use the pass1 severity (critical/important/minor) or upgrade/downgrade based on validator reasoning.
- Validator `remove` items with verdict `DISAGREE`: reclassify as **invalid** severity. The reviewer was wrong - include the item in the Invalid Feedback section with the validator's reasoning as the recommended action.
- Validator `remove` items with verdict `MINOR/NITPICK`: reclassify as **nitpick** severity. Include in the Nitpick Feedback section.
- Validator `remove` items with verdict `ALREADY FIXED`: move to the Handled Feedback section (same as resolved threads).
- Validator `remove` items with verdict `DUPLICATE`: omit (true duplicates within the same batch are the only items that get dropped).
- Validator `remove` items with verdict `OUT OF SCOPE`: reclassify as **nitpick** with a note that it's out of scope for this PR.
- Validator `clarify` items: keep at their pass1 severity, note the uncertainty in the recommended action.

For each item, retrieve its original fields (`severity`, `title`, `additional_notes`, `suggested_solution`, `recommended_action`, `reviewer_tags`, `comment_url`, `comment_ids`, etc.) from the pass1 output - the validator provides verdicts and reasoning but does not preserve these fields. Use the validator output to refine severity and recommended actions; use the pass1 output to fill in the finding details. Do NOT add your own observations or findings. If no validator result exists, output `DELEGATION_FAILURE: no validator output` and stop.

**IMPORTANT**: For each reviewer finding, always write both:
- `**Comment**: <url>` -- use `comment_url` from the pass1 JSON. This is the clickable link to the GitHub comment.
- `**Comment IDs**: 12345,67890` -- use the `comment_ids` array from the pass1 JSON, joined by commas. For deduped multi-reviewer items, include all reviewers' comment IDs. This is used by the HTML converter for exact sidecar matching to inject the correct original comment(s). Without this, the converter falls back to imprecise line-range matching which can show the wrong original comment for adjacent findings in the same file.

**Reviewer comments rendering**: Use the pass1 agent's `reviewer_comments` array to build the blockquote section. Each entry's `text` is the agent's concise summary of what the reviewer said - render it with `> **Reviewer Name**:` attribution (see the file format spec). Keep these short - this is the summary the user sees at a glance. The full original comment text (with code suggestions, AI prompts, etc.) is preserved separately in the `.feedback.json` sidecar file and injected by the HTML converter as an expandable section - the orchestrator does not need to handle that.

Populate the `## Intent` section with the intent synthesis from Step 4a.
Populate the `## Changes` section with the changes summary from Step 4.
Populate the `## Risk` section with the risk summary sentence from Step 4b-4c.
Populate the `## Results` section with a one-to-two sentence summary of what the analysis found - the overall quality signal of the reviewer feedback (e.g., "Two confirmed bugs requiring fixes before merge, plus minor style feedback.").

If there were resolved review threads from Step 3, add a `## Handled Feedback` section. Include a summary line ("N issues from reviewers were already resolved or addressed") followed by `### H1. [Brief description]` entries for each, with the file, reviewer, and resolution status.

**Question Feedback**: If pass1 returned any `question_items`, add a `## Question Feedback` section. Each question uses ID `Q1`, `Q2`, etc. Field order: `**File**:` (when pass1 provides a non-null file), `**Comment**:`, `**Comment IDs**:`, `**Reviewer**:`, then the blockquote. After the blockquote, if pass1 provided a non-null `proposed_answer`, add a `**Proposed answer**:` line with the answer text. No `**Recommended action**:` field.

**Positive Comments**: If pass1 returned any `praise_items`, add a `## Positive Comments` section. Each uses ID `P1`, `P2`, etc. Field order: `**File**:` (when pass1 provides a non-null file), `**Comment**:`, `**Comment IDs**:`, `**Reviewer**:`, then the blockquote. No `**Recommended action**:` field.

Write the respond file to `.code-reviews/<pr-number>-respond-<YYYY-MM-DD-HHMM>.md` (create the `.code-reviews/` directory if it doesn't exist).

**CRITICAL - Copy feedback sidecar immediately after writing the .md file:**
```bash
cp .code-reviews/.fetch-pending.json .code-reviews/<pr-number>-respond-<YYYY-MM-DD-HHMM>.feedback.json
```
This MUST happen before Step 8. Without it, the HTML report will have no "Original Comment" sections and the report loses significant value. Never reproduce this JSON by hand - comment IDs are large integers that LLMs hallucinate when transcribed.

## Step 8: Present Results

Present the analysis to the user in the terminal. Include:

1. **Header**: PR title/number, risk score, recommendation
2. **Finding counts** by severity (critical, important, minor, nitpick, invalid)
3. **Each finding** with:
   - ID and title (e.g. `A1 - Sort comparator inverted`)
   - Reviewer tags (e.g. `[Jamie R.] [CodeRabbit]`)
   - File and line number (e.g. `UserService.php:176`)
   - One-sentence problem description
   - One-sentence suggested change
   - Recommended action (the senior dev assessment)
4. **Handled feedback**: count and one-line summary if present
5. **Checklist**: the label + status pairs

This is the primary way the user reads the analysis in their terminal. The HTML report is a secondary reference. Do not omit finding details to save space - the user needs reviewer attribution, file, line, problem, suggestion, and recommended action for each finding to act on the analysis.

Then generate the HTML report:
```bash
python3 "$SKILL_DIR/scripts/respond-to-html.py" <respond-file.md>
```

Ask via AskUserQuestion: "Open the interactive HTML report in your browser?" with default "Open in browser" and options:
- "Open in browser"
- "Skip (saved to <path>)"

If the user chooses "Open in browser":
```bash
open <respond-file.html>
```

If the user chooses "Skip", just confirm the file path so they can open it later.

## Step 9: Acting on Findings

After the report is presented, the user may ask to fix specific issues (e.g., "fix B1", "fix the critical issues", "address the feedback"). When this happens:

1. **Read the respond file** (`.code-reviews/<pr-number>-respond-*.md`) to get the full finding details.
2. **Use the reviewer comments verbatim** as guidance. CodeRabbit and other automated reviewers include structured fix suggestions (` ```suggestion ` blocks) and "Prompt for AI Agents" sections with specific instructions for how to fix each issue. These are preserved in the report's blockquote sections.
3. **Prioritize the reviewer's suggested fix** over inventing your own approach. The reviewer saw the exact diff context and their suggestion is usually precise.
4. **Check "Also applies to" references** in CodeRabbit comments - the same pattern may need fixing in multiple locations.
5. **Read the actual code** at the referenced file and lines before making changes - the reviewer's line numbers refer to the PR diff, which may differ from the current working tree.

---

## Usage Examples

```
/arc-pr-respond 123                              # All feedback on PR #123
/arc-pr-respond https://github.com/.../pull/123  # Specific PR by URL
/arc-pr-respond 123 humans                       # Exclude bot feedback
/arc-pr-respond 123 brian                        # Only Brian's feedback
/arc-pr-respond --reviewers=brian,sarah 123      # Multiple specific reviewers
/arc-pr-respond -t 123                           # Show timestamps
/arc-pr-respond -h                               # Show help
```
