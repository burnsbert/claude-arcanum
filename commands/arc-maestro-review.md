---
description: Code review and PR creation — two-pass review with enhanced bug-finding, fixes bugs with regression tests, creates PR. Runs Phases 8-10 of the Maestro pipeline.
allowed-tools: "*"
argument-hint: [story-id]
---

# Arc Maestro Review - Code Review and PR Creation

Input: {{args}}

This command orchestrates Phases 8-10 of the Maestro development pipeline. It performs a two-pass code review with enhanced bug-finding, fixes any concerns with regression tests for bugs, and creates a pull request.

```
Phase 8: Code Review -> Phase 9: Respond (if needed) -> Phase 10: Complete (commit, push, PR)
```

This command **always runs fresh** from Phase 8, even if previously executed. No resume logic — each invocation performs a complete review cycle.

### The 3 Phases

| Phase | Name | What Happens | User Checkpoint? |
|-------|------|-------------|------------------|
| 8 | Code Review | Two-pass review: scan all files, flag concerns, validate findings | No |
| 9 | Respond | Fix validated concerns, add regression tests for bugs | No (conditional) |
| 10 | Complete | Commit review fixes, push, create PR | No |

### Prerequisites

**Phase 7 must be complete.** Development must be done. If Phase 7 is incomplete or in progress, this command will tell you to finish development first via `/arc-maestro` or `/arc-maestro {STORY-ID}`.

---

## PHASE 8: Code Review

### Step 8.1: Story ID Detection

Parse `$ARGUMENTS` (the `{{args}}` value):

**If argument provided**:
- Use it as the story ID
- Expected format: `PROJ-123` or `FILE-MY-STORY`

**If no argument**:
- Find the most recent context file:
  ```bash
  ls -t .maestro/context-*.md 2>/dev/null | head -1
  ```
- Extract story ID from filename: `.maestro/context-{STORY-ID}.md` -> `{STORY-ID}`
- If no context file found: "No Maestro context file found. Run /arc-maestro first, or provide a story ID."

### Step 8.2: Validate Phase 7 Completion

Read `.maestro/context-{STORY-ID}.md` and parse the "Current Status" section:
- Extract **Phase** field
- Extract **Progress** field

**Check Phase 7 completion**:
- Phase must be "Phase 7: Develop" or later (Phase 8, 9, 10)
- Progress must indicate completion: "All tasks completed", "Development complete", or similar (NOT "in progress", "task N/M", or "starting")

**If Phase 7 is not complete**:
```
Development is not complete for {STORY-ID}.

Current phase: {Phase}
Current progress: {Progress}

Please finish development first:
- Run /arc-maestro {STORY-ID} to resume development
- Or complete the remaining tasks manually

Code review cannot proceed until Phase 7 is complete.
```
**STOP** — do not proceed.

**If Phase 7 is complete**: Proceed to Step 8.3.

### Step 8.3: Report Review Start

Display to user:
```
Maestro Code Review for {STORY-ID}

Phase 7 status: {Progress}
Starting two-pass code review...
```

### Step 8.4: Update Context

Edit `.maestro/context-{STORY-ID}.md` to update Current Status:
- **Phase**: Phase 8: Code Review
- **Progress**: Running two-pass code review
- **Last Updated**: {timestamp}
- **Next Action**: Waiting for code reviewer to complete

### Step 8.5: Launch Code Review Agent

Use the Task tool to launch the code reviewer:
- `subagent_type`: `"ca-maestro-code-review"`
- Prompt:

```
Perform two-pass code review for story {STORY-ID}.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Read the context file for story details, acceptance criteria, scout research, and implementation summary. Use `<!-- @tag -->` anchors to extract specific sections (e.g., `sed -n '/<!-- @research -->/,/<!-- @/p' file | sed '$d'`). Read the diary for implementation context and decisions. Perform Pass 1 (scan all changed files, flag concerns), then Pass 2 (validate each concern with enhanced bug-finding). Write the review report to the context file under a `<!-- @review -->` anchored "Code Review Report" section. Update the diary with review findings.
```

Wait for completion.

### Step 8.6: Read Review Report

Read the updated context file. Extract the "Code Review Report" section.

Parse:
- **Total concerns found**: Count of validated concerns
- **Bugs found**: Count of concerns categorized as bugs
- **Other concerns**: Count of non-bug concerns

### Step 8.7: Report Review Results

Display to user:
```
Phase 8 complete. Code review done.

Review summary:
- Total concerns: {N}
- Bugs: {B}
- Other concerns: {O}
```

**DO NOT pause** — proceed to Phase 9 logic.

---

## PHASE 9: Respond (Conditional)

### Step 9.1: Check If Response Needed

Read the "Code Review Report" section from the context file.

**If no concerns found** (report indicates "0 concerns" or "Clean review"):
- Display: `Clean review — no concerns found! Skipping to PR creation...`
- Skip to Phase 10

**If concerns found**: Proceed to Step 9.2.

### Step 9.2: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 9: Respond
- **Progress**: Fixing code review concerns
- **Last Updated**: {timestamp}
- **Next Action**: Waiting for code review responder to address concerns

### Step 9.3: Display Progress

```
Phase 9: Addressing code review concerns...
```

### Step 9.4: Launch Code Review Responder Agent

Use the Task tool:
- `subagent_type`: `"ca-maestro-code-review-responder"`
- Prompt:

```
Address code review concerns for story {STORY-ID}.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Read the context file's Code Review Report section for all validated concerns. Read the diary for implementation context. Fix each concern:
- For bugs: implement fix + regression test
- For other concerns: implement fix

Update the diary with fixes and decisions. Work autonomously through all concerns.
```

Wait for completion.

### Step 9.5: Report Response Complete

Display to user:
```
Phase 9 complete. All code review concerns addressed.
```

**DO NOT pause** — proceed to Phase 10.

---

## PHASE 10: Complete

### Step 10.1: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 10: Complete
- **Progress**: Committing changes, creating PR
- **Last Updated**: {timestamp}
- **Next Action**: Commit, push, create PR

### Step 10.2: Check If Review Changes Were Made

Read the diary file to determine if Phase 9 ran (check for entries from `ca-maestro-code-review-responder`).

**If Phase 9 ran** (concerns were fixed): Proceed to Step 10.3.

**If Phase 9 was skipped** (clean review): Skip to Step 10.4 (no review commit needed).

### Step 10.3: Commit Review Fixes

Stage and commit the review changes:

```bash
git add -A && git commit -m "$(cat <<'EOF'
{STORY-ID}: Address code review feedback

{Summary of what was fixed from the diary/report}

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

If commit fails (no changes to commit):
- This is fine — responder may have only run tests, no actual changes
- Log to diary: `[learning] No code changes from review response (tests passed, no fixes needed).`
- Continue to Step 10.4

### Step 10.4: Push to Remote

```bash
git push
```

If push fails:
- Display error to user
- Suggest: `git push -u origin {branch-name}` if branch not tracking remote
- **WAIT for user to resolve push issue**
- Once resolved, continue to Step 10.5

### Step 10.5: Prepare PR Body

Read the context file and extract:
- Story title
- Story description (summary of what was implemented)
- Completed tasks list (from "Completed Tasks" section)
- Code review results (from "Code Review Report" section)

Count:
- Total tasks completed
- Bugs fixed in review
- Other concerns addressed in review

Generate PR body:

```markdown
## Summary
{Brief description of what was implemented — 1-2 sentences from story title and description}

## Changes
{List of main changes — derive from completed tasks list, 3-7 bullet points}

## Testing
- All unit tests passing
- Code review: {X} bugs fixed with regression tests, {Y} concerns addressed

## Story
{STORY-ID}

Generated with Maestro
```

### Step 10.6: Create Pull Request

Use `gh` CLI to create the PR:

```bash
gh pr create --title "{STORY-ID}: {Story title}" --body "$(cat <<'EOF'
{The PR body from Step 10.5}
EOF
)"
```

**If `gh` command fails**:
- Check if `gh` CLI is installed: `which gh`
- Check if authenticated: `gh auth status`
- If not installed or not authenticated, display:
  ```
  GitHub CLI (gh) is not available or not authenticated.

  To create the PR:
  1. Install gh: https://cli.github.com/
  2. Authenticate: gh auth login
  3. Then run: gh pr create --title "{STORY-ID}: {Story title}" --body "{PR body}"

  Alternatively, create the PR manually via GitHub web UI.
  ```
- **WAIT for user**
- If user creates PR manually, ask for PR URL to continue

Capture the PR URL from `gh pr create` output.

### Step 10.7: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Progress**: Complete — PR created
- **Last Updated**: {timestamp}
- **Next Action**: Review the PR at {PR URL}

### Step 10.8: Update Diary

Append to `.maestro/diary-{STORY-ID}.md`:

```markdown
## [{timestamp}] arc-maestro-review
[success] Maestro pipeline complete. Code reviewed, concerns addressed, PR created: {PR URL}
---
```

### Step 10.9: Display Final Report

```
## Maestro Complete

Story: {STORY-ID} - {Story title}

Code review:
- Total concerns: {N}
- Bugs fixed: {B} (with regression tests)
- Other concerns: {C}

Pull request created: {PR URL}

Next step: Review the PR and merge when ready!
```

---

## Error Handling

### Phase 7 Not Complete

If Step 8.2 validation fails:
- Display clear message with current phase and progress
- Tell user to run `/arc-maestro {STORY-ID}` to resume development
- **STOP** — do not proceed

### Missing Context File

If story ID is provided but context file doesn't exist:
```
Context file not found for {STORY-ID}.

Expected: .maestro/context-{STORY-ID}.md

Either:
1. The story ID is incorrect
2. Maestro was never run for this story
3. The context file was deleted

Run /arc-maestro {STORY-ID} to start fresh.
```
**STOP** — do not proceed.

### Agent Failures

If `ca-maestro-code-review` or `ca-maestro-code-review-responder` fails:
1. Log error to diary with `[problem]` tag
2. Display error to user with agent name and failure reason
3. Suggest: "Retry /arc-maestro-review {STORY-ID} or investigate the failure manually."
4. **STOP** — user must decide how to proceed

### Git Push Failure

If `git push` fails:
- Display the git error message
- Common issues:
  - Branch not tracking remote: Suggest `git push -u origin {branch-name}`
  - Authentication issues: Suggest `git config` or credential helper
  - Merge conflicts with remote: Suggest pulling and resolving conflicts
- **WAIT for user to resolve**
- User can re-run `/arc-maestro-review {STORY-ID}` after fixing git issues

### PR Creation Failure

If `gh pr create` fails:
- Check if `gh` is installed and authenticated
- If not: provide instructions and alternative (manual PR creation)
- If `gh` fails for other reasons: display error, suggest manual PR creation
- **WAIT for user**

### Corrupted Context File

If context file exists but is unreadable or missing critical sections:
- Report which sections are missing
- Suggest manual review of `.maestro/context-{STORY-ID}.md`
- **STOP** — cannot proceed without valid context

---

## Implementation Notes

### Always Fresh Execution

This command does NOT resume from previous runs. Every invocation:
1. Starts from Phase 8
2. Re-runs the full code review
3. Re-fixes any concerns found
4. Re-creates the PR (or updates if draft exists)

**Why no resume?** Code review should always see the latest state. If concerns were fixed manually between runs, the review will catch that and report "Clean review."

### Continuous Execution

This command runs autonomously from start to finish. **DO NOT pause for user confirmation** between phases. The only user interactions are:
- Error conditions (Phase 7 not complete, git push failure, PR creation failure)
- Manual PR creation fallback

### Tech-Stack Agnostic

This command makes zero assumptions about:
- Language or framework
- Test runner or test file conventions
- Git hosting (relies on `gh` CLI which supports GitHub)
- CI/CD systems

All project-specific knowledge comes from the scout's research (stored in context file).

### Context vs Diary Methodology

- **Context file**: Status dashboard. Updated with phase progress, review report, final status.
- **Diary file**: Narrative log. Written when review finds insights, when fixes are applied, when problems occur.
- **Todo file**: Task list. Not modified during review phases (read-only reference).

### Diary Entry Format

All diary entries use this format with grep-able tags:
```
## [{timestamp}] {agent-name}
[tag] Description of what happened.
---
```

Tags: `[decision]`, `[problem]`, `[learning]`, `[success]`

### Agent Routing Summary

| Phase | Agent | Model | Task |
|-------|-------|-------|------|
| 8 | `ca-maestro-code-review` | Opus | Two-pass review with enhanced bug-finding |
| 9 | `ca-maestro-code-review-responder` | Opus | Fix concerns, add regression tests for bugs |

### Token Cost Profile

- Phase 8: 1 code review call (Opus) — scans all changed files, validates concerns
- Phase 9: 0-1 responder call (Opus) — only if concerns found
- Total: 1-2 agent calls per review run

---

## Example User Experiences

### Clean Review (No Concerns)

```
User: /arc-maestro-review PROJ-123

Claude: Maestro Code Review for PROJ-123

        Phase 7 status: All tasks completed
        Starting two-pass code review...

        Phase 8 complete. Code review done.

        Review summary:
        - Total concerns: 0
        - Bugs: 0
        - Other concerns: 0

        Clean review — no concerns found! Skipping to PR creation...

        ## Maestro Complete

        Story: PROJ-123 - Add user authentication

        Code review:
        - Total concerns: 0
        - Bugs fixed: 0
        - Other concerns: 0

        Pull request created: https://github.com/org/repo/pull/456

        Next step: Review the PR and merge when ready!
```

### Review With Concerns

```
User: /arc-maestro-review PROJ-123

Claude: Maestro Code Review for PROJ-123

        Phase 7 status: All tasks completed
        Starting two-pass code review...

        Phase 8 complete. Code review done.

        Review summary:
        - Total concerns: 5
        - Bugs: 2
        - Other concerns: 3

        Phase 9: Addressing code review concerns...

        Phase 9 complete. All code review concerns addressed.

        ## Maestro Complete

        Story: PROJ-123 - Add user authentication

        Code review:
        - Total concerns: 5
        - Bugs fixed: 2 (with regression tests)
        - Other concerns: 3

        Pull request created: https://github.com/org/repo/pull/456

        Next step: Review the PR and merge when ready!
```

### No Argument (Most Recent Story)

```
User: /arc-maestro-review

Claude: [Finds .maestro/context-PROJ-123.md as most recent]

        Maestro Code Review for PROJ-123
        [... continues as normal ...]
```

### Phase 7 Not Complete

```
User: /arc-maestro-review PROJ-123

Claude: Development is not complete for PROJ-123.

        Current phase: Phase 7: Develop
        Current progress: Task 5/8 in progress

        Please finish development first:
        - Run /arc-maestro PROJ-123 to resume development
        - Or complete the remaining tasks manually

        Code review cannot proceed until Phase 7 is complete.
```

### Git Push Failure

```
User: /arc-maestro-review PROJ-123

Claude: [... review and fixes complete ...]

        [git push fails with "no upstream branch" error]

        Git push failed:
        fatal: The current branch proj-123-add-user-auth has no upstream branch.

        To push the current branch and set the remote as upstream, use:
            git push -u origin proj-123-add-user-auth

User: [Runs the suggested command]
      git push -u origin proj-123-add-user-auth

User: /arc-maestro-review PROJ-123

Claude: [Re-runs, push succeeds this time]

        ## Maestro Complete
        [... PR created ...]
```

### GitHub CLI Not Available

```
User: /arc-maestro-review PROJ-123

Claude: [... review and push complete ...]

        GitHub CLI (gh) is not available or not authenticated.

        To create the PR:
        1. Install gh: https://cli.github.com/
        2. Authenticate: gh auth login
        3. Then run: gh pr create --title "PROJ-123: Add user authentication" --body "[PR body]"

        Alternatively, create the PR manually via GitHub web UI.

User: [Creates PR manually via web UI]

User: /arc-maestro-review PROJ-123

Claude: [Re-runs, this time with gh installed and authenticated]

        ## Maestro Complete
        [... PR created via CLI ...]
```
