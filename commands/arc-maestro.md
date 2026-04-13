---
description: Semi-autonomous development pipeline — researches codebase, creates plan, implements tasks with specialist routing, validates each task. Takes a story from Jira or local file through 7 phases to implementation.
allowed-tools: "*"
argument-hint: <story-id or filepath>
---

# Arc Maestro - Semi-Autonomous Development Pipeline

Input: {{args}}

This command orchestrates Phases 1-7 of the Maestro development pipeline. It takes a story (from Jira or a local file), researches the codebase, creates a plan, gets user approval, and implements every task with mandatory validation. Specialized agents are routed based on task type and difficulty.

```
Initialize -> Scout -> Questions? -> Plan -> Review -> Approve -> Develop (task-by-task with validation)
```

### The 7 Phases

| Phase | Name | What Happens | User Checkpoint? |
|-------|------|-------------|------------------|
| 1 | Initialize | Fetch story, create branch, create context/diary files | No |
| 2 | Scout | Research codebase patterns, conventions, test coverage | No |
| 3 | Questions | Present scout's ambiguities to user for answers | Yes (if ambiguities exist) |
| 4 | Plan | Break story into tasks with difficulty/type/TDD structure | No |
| 5 | Review | Quality gate: plan-reviewer vets and improves the plan | No |
| 6 | Approve | User reviews and approves the plan | Yes |
| 7 | Develop | Implement tasks one-by-one with mandatory validation | Yes (only on blocker) |

After Phase 7, point the user to `/arc-maestro-review` for code review (Phases 8-10).

### Continuous Execution

Maestro runs autonomously between user checkpoints. **DO NOT pause for confirmation** between Phases 2->3->4->5 or between individual tasks in Phase 7. The only user checkpoints are:
- Phase 3 (if scout has unanswered questions)
- Phase 6 (plan approval)
- Phase 7 (only if a task fails 3 times)

---

## PHASE 1: Initialize

### Step 1.1: Parse Input

Parse `$ARGUMENTS` (the `{{args}}` value) to determine story source:

**File path detection** (check first):
- Argument contains `/`
- Argument starts with `./` or `~`
- Argument ends with `.md` or `.txt`

If any of these match: treat as file path. Story ID = `FILE-{FILENAME-UPPERCASE}` (strip extension, replace non-alphanumeric with `-`, uppercase). Skip Jira entirely.

**Jira ID detection** (check second):
- Argument matches pattern `[A-Z]+-[0-9]+` (e.g., `PROJ-123`, `ARC-7800`)

If match: treat as Jira ticket.

**Neither matches**:
- Say: "Maestro requires a story. Provide a Jira ID (e.g., PROJ-123) or a file path (e.g., ./stories/my-story.md)."
- **WAIT for user response**
- Re-parse the response with the same rules

### Step 1.2: Resume Check

Before doing anything else, check if a context file already exists:

```bash
ls .maestro/context-{STORY-ID}.md 2>/dev/null
```

**If context file exists**:
1. Read `.maestro/context-{STORY-ID}.md`
2. Parse the "Current Status" section: extract **Phase**, **Progress**, **Next Action**
3. Display to user:
   ```
   Existing Maestro session found for {STORY-ID}:
   Phase: {phase}
   Progress: {progress}
   Next Action: {next action}

   Resume from where you left off, or start fresh?
   ```
4. **WAIT for user response**
5. If **resume**: jump to the appropriate phase based on "Phase" value:
   - "Phase 1: Initialize" -> Phase 2 (initialization was done)
   - "Phase 2: Scout" -> Phase 2
   - "Phase 3: Questions" -> Phase 3
   - "Phase 4: Plan" -> Phase 4
   - "Phase 5: Review" -> Phase 5
   - "Phase 6: Approve" -> Phase 6
   - "Phase 7: Develop" -> Phase 7 (pick up from the current/next uncompleted task)
     **Restore state**: Read `.maestro/state-{STORY-ID}.json` if it exists. Use it to restore `current_task_index`, `failure_counts`, and `deferred_tasks`. Then scan the todo file from task `current_task_index` onward for the first task still marked `- [ ]`. If `current_task_index` already points to a `- [x]` task (state was incremented right before the crash), advance to the next `- [ ]` task. If the state file doesn't exist (older session), fall back: tasks marked `- [x]` with a receipt file but NOT listed in the context file's "Completed Tasks" section were deferred and never batch-validated — add them back to `deferred_tasks`.
6. If **start fresh**: Delete existing Maestro files for this story:
   ```bash
   rm -f .maestro/context-{STORY-ID}.md .maestro/diary-{STORY-ID}.md .maestro/todo-{STORY-ID}.md .maestro/summary-{STORY-ID}.md .maestro/task-{STORY-ID}-*.md .maestro/state-{STORY-ID}.json
   ```
   Then continue with Step 1.3.

**If no context file**: Continue to Step 1.3.

### Step 1.3: Branch Handling

1. **Get current branch**:
   ```bash
   git branch --show-current
   ```

2. **Check if already on the correct branch**:
   - Convert story ID to lowercase (e.g., `PROJ-123` -> `proj-123`, `FILE-MY-STORY` -> `file-my-story`)
   - If current branch starts with the lowercase story ID -> already on correct branch. Proceed.

3. **Check if matching branch exists**:
   ```bash
   git branch --list "*{lowercase-story-id}*"
   ```
   - If a matching branch exists -> show it to user, ask: "Branch `{branch-name}` exists for this story. Switch to it?"
   - **WAIT for user response**
   - If yes: `git checkout {branch-name}`

4. **Create new branch if needed**:
   - Detect base branch (check in order, use first that exists):
     ```bash
     git branch --list "development" || git branch --list "develop" || git branch --list "main" || git branch --list "master"
     ```
     Also check remote branches:
     ```bash
     git branch -r --list "origin/development" || git branch -r --list "origin/develop" || git branch -r --list "origin/main" || git branch -r --list "origin/master"
     ```
   - Generate branch name: `{lowercase-story-id}-{2-4-word-kebab-description}`
     - Derive the description from the story title (once loaded)
     - Example: `proj-123-add-user-auth`, `file-my-story-implement-feature`
   - Create and switch: `git checkout -b {branch-name} {base-branch}`

### Step 1.4: Load Story

**For file-based stories**:
1. Read the file
2. Extract:
   - **Title**: First heading (line starting with `#`). If no heading, use the filename.
   - **Description**: Body text (everything after the title, excluding AC section)
   - **Acceptance Criteria**: Look for a section labeled "Acceptance Criteria", "ACs", or similar. If none found, note "Not specified."
   - **Type**: Default to "Story"
   - **Priority**: "Not specified"
   - **Status**: "Not specified"

**For Jira tickets**:
1. Try to fetch via MCP tools:
   - Try `mcp___jira-read__get-issue` with the story ID
   - If that fails, try `mcp___jira__get-issue`
2. Extract: title, description, acceptance criteria, type, status, priority
3. **If Jira MCP tools are unavailable or ticket not found**:
   - Check for a matching file in `.stories/` directory:
     ```bash
     ls .stories/{STORY-ID}.md .stories/{STORY-ID}.txt .stories/{lowercase-story-id}.md 2>/dev/null
     ```
   - Check project root for matching file
   - If found, load as file-based story
   - If nothing found: report error and stop

### Step 1.5: Create `.maestro/` Directory

```bash
mkdir -p .maestro
```

### Step 1.6: Create Context File

Create `.maestro/context-{STORY-ID}.md` with this template:

```markdown
# Maestro Context: {STORY-ID}

<!-- @story -->
## Story Details
**Source**: {Jira: STORY-ID / File: filepath}
**Title**: {title}
**Type**: {type}
**Priority**: {priority}
**Status**: {status}

**Description**:
{description}

**Acceptance Criteria**:
{acceptance criteria}

<!-- @status -->
## Current Status
**Phase**: Phase 1: Initialize
**Progress**: Story initialized
**Started**: {timestamp}
**Last Updated**: {timestamp}
**Next Action**: Launch scout agent for research

_Agents update Phase, Progress, Last Updated, and Next Action as work progresses_

<!-- @research -->
## Research Findings
_Populated by scout agent_

<!-- @tasks -->
## Task Progress

<!-- @completed -->
### Completed Tasks
_Track completed tasks with summaries as development progresses_

<!-- @current-task -->
### Current Task
_Track the task currently being worked on_

<!-- @pending -->
### Pending Tasks
_Remaining tasks from the plan_

<!-- @outputs -->
## Agent Outputs
_Agent outputs recorded here_

<!-- @blockers -->
## Blockers
_None at initialization_

<!-- @decisions -->
## Decisions
_Key decisions recorded here_
```

### Step 1.7: Create Diary File

Create `.maestro/diary-{STORY-ID}.md` with an initial entry:

```markdown
# Maestro Diary: {STORY-ID}

## [{timestamp}] arc-maestro
[decision] Initialized story {STORY-ID} from {source type: "Jira" or "file: {filepath}"}.
---
```

### Step 1.8: Report Initialization

Display to user:
```
Maestro initialized for: {title}

Story ID: {STORY-ID}
Source: {source}
Branch: {branch name}

Context: .maestro/context-{STORY-ID}.md
Diary: .maestro/diary-{STORY-ID}.md

Phase 1 complete. Launching scout...
```

### Step 1.9: Update Memory

Check your auto memory `MEMORY.md` for Maestro info. If not present, append:

```markdown
## Maestro

Semi-autonomous dev pipeline. Files live in `.maestro/`:
- `context-{ID}.md` — status dashboard (phase, research, tasks)
- `diary-{ID}.md` — append-only narrative log
- `todo-{ID}.md` — task list with checkboxes
- Check phase: `grep '^\*\*Phase\*\*:' .maestro/context-*.md`
- Run `/arc-maestro` to start/resume, `/arc-maestro-review` for code review + PR
```

**DO NOT pause for confirmation** -- proceed immediately to Phase 2.

---

## PHASE 2: Scout

### Step 2.1: Update Context

Edit `.maestro/context-{STORY-ID}.md` to update Current Status:
- **Phase**: Phase 2: Scout
- **Progress**: Scout researching codebase
- **Last Updated**: {timestamp}
- **Next Action**: Waiting for scout to complete research

### Step 2.2: Launch Scout Agent

Use the Task tool to launch the scout:
- `subagent_type`: `"ca-maestro-scout"`
- Prompt: Include the story ID, context file path, and diary file path. Example:

```
Research the codebase for story {STORY-ID}.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file (to create later by planner): .maestro/todo-{STORY-ID}.md

Read the context file for story details and acceptance criteria. Research the codebase thoroughly:
- Analyze story type
- Run story refinement (check AC completeness, identify edge cases, flag gaps)
- Research guides/, bugfinder.md, .guide.md/CLAUDE.md, test coverage, codebase patterns
- Generate structured research report
- Update the context file's Research Findings section with your full report
- Update the diary with key research discoveries

Work autonomously -- do not ask the user questions during research.
```

Wait for completion.

### Step 2.3: Review Scout Findings

Read the updated context file. Check the Research Findings section for:
- **Unanswered Questions**: Items the scout flagged as needing user input
- **Ambiguities in Story**: Gaps that need clarification
- **Story Gaps Requiring Clarification**: Issues requiring PM or user decision

If any exist -> proceed to Phase 3.
If none -> skip Phase 3, proceed directly to Phase 4.

### Step 2.4: Generate Research Summary

Read the Research Findings section from the context file and condense it into `.maestro/summary-{STORY-ID}.md`. This file is the primary research reference for all dev-doer agents — it saves them from reading the full context file every time.

```bash
sed -n '/<!-- @research -->/,/<!-- @/p' .maestro/context-{STORY-ID}.md | sed '$d'
```

Write a condensed summary (~50 lines):

```markdown
# Research Summary: {STORY-ID}

## Story Type
{FE-only / BE-only / Full-stack / Bug fix}

## Key Patterns
- {Pattern 1}: `file.ext:line` — {brief description}
- {Pattern 2}: `file.ext:line` — {brief description}

## Testing Strategy
- **File types WITH test patterns** (TDD mandatory): {list}
- **File types WITHOUT test patterns**: {list}
- **Test command**: {e.g., vendor/bin/phpunit, npm test}

## Implementation Approach
{3-5 bullet points summarizing the recommended approach}

## Key Citations
- {Most important file references dev-doers will need}

## Constraints & Gotchas
- {Important constraints or warnings from scout research}

## User Decisions
{Decisions recorded in Phase 3, or "None" if Phase 3 was skipped}

_Full research: `.maestro/context-{STORY-ID}.md` — use `<!-- @research -->` section or grep for details not covered here_
```

### Step 2.5: Display Progress

```
Phase 2 complete. Scout research done.
{Brief summary of what was found: story type, key patterns, test coverage insights}
```

**DO NOT pause** -- flow directly to Phase 3 (if needed) or Phase 4.

---

## PHASE 3: Questions (Conditional)

This phase only runs if the scout identified unanswered questions or ambiguities.

### Step 3.1: Present Questions

Compile all questions from the scout's report:
- Unanswered Questions
- Ambiguities in Story
- Story Gaps Requiring Clarification

Present them to the user in a numbered list, with the scout's context/recommendation for each:

```
The scout identified {N} questions that need your input:

1. {Question title}
   Context: {scout's explanation}
   Recommendation: {scout's suggestion}

2. {Question title}
   ...

Please answer each question (or say "use recommendation" to accept the scout's suggestion).
```

### Step 3.2: Wait for Answers

**WAIT for user response.**

### Step 3.3: Record Decisions

For each answer:
1. Add to the **Decisions** section of the context file:
   ```
   {N}. **{Question title}**: {user's answer or accepted recommendation}
   ```
2. Append to the diary:
   ```
   ## [{timestamp}] arc-maestro
   [decision] User answered scout questions: {brief summary of decisions}.
   ---
   ```
3. Update the **User Decisions** section of `.maestro/summary-{STORY-ID}.md`:
   - Replace the placeholder with the actual decisions (same format as recorded in the context file)
   - This ensures dev-doers reading the summary first see the correct decisions

### Step 3.4: Update Context and Proceed

Update context file:
- **Phase**: Phase 3: Questions
- **Progress**: User questions answered, proceeding to planning
- **Last Updated**: {timestamp}
- **Next Action**: Launch planner agent

**DO NOT pause** -- proceed directly to Phase 4.

---

## PHASE 4: Plan

### Step 4.1: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 4: Plan
- **Progress**: Planner creating task breakdown
- **Last Updated**: {timestamp}
- **Next Action**: Waiting for planner to create task list

### Step 4.2: Launch Planner Agent

Use the Task tool:
- `subagent_type`: `"ca-maestro-planner"`
- Prompt:

```
Create the implementation plan for story {STORY-ID}.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file to create: .maestro/todo-{STORY-ID}.md

Read the context file completely -- story details, scout research, user decisions. Create a structured task breakdown in the todo file with difficulty ratings, type tags, and TDD requirements based on scout's test coverage insights. Update the context file with planning status and write to the diary with planning decisions.
```

Wait for completion.

### Step 4.3: Display Progress

```
Phase 4 complete. Plan created with {N} tasks.
```

**DO NOT pause** -- proceed directly to Phase 5.

---

## PHASE 5: Review

### Step 5.1: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 5: Review
- **Progress**: Plan reviewer improving the plan
- **Last Updated**: {timestamp}
- **Next Action**: Waiting for plan reviewer to complete

### Step 5.2: Launch Plan Reviewer Agent

Use the Task tool:
- `subagent_type`: `"ca-maestro-plan-reviewer"`
- Prompt:

```
Review and improve the implementation plan for story {STORY-ID}.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Review the plan across all dimensions (scout research quality, plan quality, cross-cutting concerns). Apply ALL improvements directly to the todo file -- add missing tasks, remove unnecessary ones, improve descriptions, fix TDD requirements, add citations. Add review summary to the context file under "Plan Review" section. Write to the diary with review findings and reasoning.
```

Wait for completion.

### Step 5.3: Display Progress

```
Phase 5 complete. Plan reviewed and improved.
```

**DO NOT pause** -- proceed directly to Phase 6.

---

## PHASE 6: Approve

### Step 6.1: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 6: Approve
- **Progress**: Waiting for user approval of plan
- **Last Updated**: {timestamp}
- **Next Action**: User reviewing plan

### Step 6.2: Present Plan to User

Read `.maestro/todo-{STORY-ID}.md` and display the full plan to the user:

```
## Implementation Plan for {STORY-ID}

{Display the complete todo file content}

---

Review the plan above. You can:
- **Approve** -- proceed to implementation
- **Request changes** -- describe what to modify
```

### Step 6.3: Wait for Approval

**WAIT for user response.**

### Step 6.4: Handle Response

**If approved** (user says "approve", "approved", "looks good", "LGTM", "go", "yes", or similar affirmative):
1. Update context:
   - **Progress**: Plan approved by user
   - **Next Action**: Begin development
2. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [decision] User approved the implementation plan.
   ---
   ```
3. Proceed to Phase 7.

**If changes requested**:
1. Apply the requested changes to `.maestro/todo-{STORY-ID}.md` using Edit tool
2. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [decision] User requested plan changes: {brief summary}. Applied modifications.
   ---
   ```
3. Re-display the updated plan to user (loop back to Step 6.2)

**Loop until approved.**

---

## PHASE 7: Develop

### Step 7.1: Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 7: Develop
- **Progress**: Starting task-by-task implementation
- **Last Updated**: {timestamp}
- **Next Action**: Route and implement first task

### Step 7.2: Parse Task List

Read `.maestro/todo-{STORY-ID}.md`. Extract all tasks (lines matching `- [ ]` checkbox pattern). For each task, parse:
- **Task number**: Sequential position
- **Description**: The task text
- **Type tag**: `[Type: frontend]` or `[Type: devops]` (if present)
- **Difficulty rating**: `[Difficulty: N/10]`
- **Notes**: Any indented content below the task line

Track:
- `total_tasks`: Total number of tasks
- `current_task_index`: 1-based position of the task currently being executed (or about to execute). Updated to N+1 only after a task's completion diary entry is written — so a mid-task crash always resumes at the correct task.
- `failure_counts`: Map of task index to number of failures (starts at 0)
- `deferred_tasks`: List of tasks deferred to batch validation `{task_number, description}` (starts empty)

Note: `task_number`, `N`, and `current_task_index` are used interchangeably throughout Phase 7 — all refer to the 1-based sequential position of a task in the todo file. `current_task_index` is the authoritative variable name for in-memory tracking; `N` appears in file path templates; `task_number` appears in the `deferred_tasks` array entries.

After parsing, write the initial state file using the Write tool (substitute actual computed integer values):

```json
{"current_task_index": 1, "total_tasks": {TOTAL_TASKS_COUNT}, "failure_counts": {}, "deferred_tasks": []}
```

### Step 7.3: Task Execution Loop

For each uncompleted task in the todo list:

#### A. Route Task

Determine which agent to use. **Two-dimensional routing -- check type tag FIRST:**

1. **Type tag check** (takes priority over difficulty):
   - Task has `[Type: frontend]` -> use `ca-maestro-frontend-dev-doer`
   - Task has `[Type: devops]` -> use `ca-maestro-devops-dev-doer`

2. **Difficulty rating** (fallback for untagged tasks):
   - Difficulty 7 or higher -> use `ca-maestro-senior-dev-doer`
   - Difficulty 4-6 -> use `ca-maestro-dev-doer`
   - Difficulty 1-3 -> use `ca-maestro-junior-dev-doer`

Display routing:
```
Task {current}/{total}: {task description}
Routing: {agent name} (reason: {type tag / difficulty N})
```

#### B. Update Context

Edit context file:
- Under **Current Task**: `Task {N}/{total}: {description}`
- **Last Updated**: {timestamp}

#### C. Launch Dev Agent

Use the Task tool:
- `subagent_type`: The agent determined in step A
- Prompt:

```
Implement task {current_task_index} of {total_tasks} for story {STORY-ID}.

Task: {full task description including notes}

Research summary: .maestro/summary-{STORY-ID}.md
Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Read the research summary first for key patterns and citations. Read the context file for full story details and completed task history. Read the diary for discoveries from earlier tasks. Implement this single task following scout research patterns and citations. When complete, write your implementation summary to `.maestro/task-{STORY-ID}-{N}.md` (include: what you built, test commands run, test output, files changed). Update the diary if you discover anything that could affect later tasks.
{If this is an escalation: "ESCALATION: This task previously failed {N} times. Previous failure reason: {reason}. Address the ROOT CAUSE, not symptoms."}
```

Wait for completion. The agent writes its receipt to `.maestro/task-{STORY-ID}-{N}.md`.

#### D. Mandatory Validation

**NEVER skip per-task validation for difficulty 4+ and specialist tasks.**

**Batch Deferral** (untagged difficulty 1-3 tasks only):
- If task has **no type tag** AND **difficulty 1-3**:
  - Add to `deferred_tasks`: `{task_number, description}` (receipt at `.maestro/task-{STORY-ID}-{N}.md`)
  - Mark `- [x]` in todo file (optimistic; batch validator verifies at end)
  - Update state file: increment `current_task_index`, add entry to `deferred_tasks` array
  - Display: `Task {N}/{total} deferred to batch validation.`
  - **Skip per-task validation. Proceed to next task.**

**Per-task validator routing** (all specialist-tagged tasks and difficulty 4+):

1. **Type tag check** (takes priority):
   - Task has `[Type: frontend]` AND difficulty 4+ -> use `ca-maestro-ui-validator`
   - Task has `[Type: frontend]` AND difficulty 1-3 -> use `ca-maestro-task-validator`
   - Task has `[Type: devops]` (any difficulty) -> falls through to difficulty-based routing below

2. **Difficulty rating** (fallback for untagged tasks and devops tasks):
   - Difficulty 7+ -> use `ca-maestro-senior-task-validator`
   - Difficulty ≤ 6 -> use `ca-maestro-task-validator`

Use the Task tool:
- `subagent_type`: The validator determined above
- Prompt:

```
Validate task {current_task_index} of {total_tasks} for story {STORY-ID}.

Task: {full task description including notes}

Dev agent receipt: .maestro/task-{STORY-ID}-{N}.md — read this file for implementation details, test commands run, test output, and files changed.

Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Read the context file's Task Progress section to understand what previous tasks accomplished. Read the receipt file for what the dev agent did. Validate this specific task: verify implementation exists, run tests independently, check full scope completion. Return COMPLETE or INCOMPLETE.
```

Wait for completion. Parse the validator's verdict: `STATUS: COMPLETE` or `STATUS: INCOMPLETE`.

#### E. Handle Validation Result

**If COMPLETE**:
1. Mark task done in todo file: change `- [ ]` to `- [x]`
2. Update context file:
   - Move task from "Current Task" to "Completed Tasks" with brief summary
   - **Last Updated**: {timestamp}
3. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [success] Task {N}/{total} completed: {brief description}.
   ---
   ```
4. Reset failure count for this task
5. Update state file: increment `current_task_index`, remove entry from `failure_counts`
6. Display: `Task {N}/{total} COMPLETE. Moving to next task...`
7. Continue to next task

**If INCOMPLETE**:
1. Increment `failure_counts[current_task_index]`
2. Update state file: write updated `failure_counts`
3. Read the validator's output for the specific failure reason

**Failure count < 3 -- retry with escalation logic:**

The retry/escalation rules differ based on whether the task has a specialist type tag:

- **Specialist tasks** (`[Type: frontend]` or `[Type: devops]`):
  - Retry with the **SAME specialist agent**. No cross-agent escalation.
  - Frontend tasks always go to `ca-maestro-frontend-dev-doer`
  - DevOps tasks always go to `ca-maestro-devops-dev-doer`

- **Untagged tasks, difficulty 4+** (routed by difficulty):
  - Failure count 1: Retry with the same agent
  - Failure count 2: **Escalate to `ca-maestro-senior-dev-doer`** regardless of original difficulty rating

- **Untagged tasks, difficulty 1-3** (junior tier):
  - Failure count 1: **Escalate to `ca-maestro-dev-doer`**
  - Failure count 2: **Escalate to `ca-maestro-senior-dev-doer`**

Include the failure context in the retry prompt (validator's reason, what was tried).

Display: `Task {N} INCOMPLETE (attempt {failure_count}/3). {Retrying with same agent / Escalating to senior dev}...`

Loop back to step C with the updated agent assignment.

**Failure count = 3 -- HALT:**
1. Update state file: write `failure_counts[current_task_index] = 3`
2. Update context file:
   - **Progress**: HALTED on task {N}
   - Add to **Blockers**: Task {N} failed 3 times: {failure reasons summary}
3. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [problem] Task {N}/{total} failed 3 times. Halting for user intervention. Failure reasons: {summary}.
   ---
   ```
4. Display to user:
   ```
   Task {N}/{total} has failed 3 times.

   Task: {description}
   Failure reasons:
   1. {Attempt 1 reason}
   2. {Attempt 2 reason}
   3. {Attempt 3 reason}

   Options:
   1. Implement this task manually, then continue (`/arc-maestro {STORY-ID}` to resume)
   2. Adjust the task scope and retry
   3. Skip this task and continue with the rest
   ```
5. **WAIT for user response**
6. Handle based on choice:
   - Manual: STOP. User will resume later.
   - Adjust scope: Edit the task in the todo file per user's instructions, reset failure count, retry
   - Skip: Mark task as skipped in todo file (`- [~]`), note in context file, continue to next task

#### F. New Task Discovery

During development, agents may discover new requirements -- technical dependencies the scout missed, edge cases that only become apparent during implementation, visual issues caught by browser verification, etc.

When a dev agent's output mentions discovering new work needed:
1. Add the new task to `.maestro/todo-{STORY-ID}.md` at an appropriate position
2. Increment `total_tasks`; write updated value to state file
3. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [learning] New task discovered during task {N}: {description}. Added to todo list.
   ---
   ```
4. Display: `New task discovered: {description}. Added to plan.`
5. The new task will be executed in sequence when reached

#### G. Visual Verification (When Applicable)

If the scout/planner indicated that visual verification is appropriate for this story (check Research Findings and todo file notes for visual verification indicators), use browser automation during Phase 7 to verify UI output:

1. After a frontend task is validated as COMPLETE, check if visual verification is indicated
2. Use Playwright MCP tools (`mcp__playwright__*`) or Claude Code browser integration to verify the UI
3. If visual verification reveals problems (broken layout, missing states, interaction issues):
   - Create new fix tasks in the todo file
   - Log the discovery in the diary
   - Execute the fix tasks as part of the current Phase 7 run
4. All verification runs **locally** -- never deploy to external systems unless the user explicitly asks

### Step 7.4: Batch Validate Deferred Tasks

If `deferred_tasks` is empty, skip to Step 7.5.

Display: `Batch validating {N} deferred tasks (difficulty 1-3)...`

Use the Task tool:
- `subagent_type`: `"ca-maestro-batch-validator"`
- Prompt:

```
Batch validate {N} deferred tasks for story {STORY-ID}.

Story ID: {STORY-ID}
Context file: .maestro/context-{STORY-ID}.md
Diary file: .maestro/diary-{STORY-ID}.md
Todo file: .maestro/todo-{STORY-ID}.md

Tasks to validate (all difficulty 1-3, no type tag):
{For each deferred task: "- Task {N}: {description}"}

Receipt files for each task are at .maestro/task-{STORY-ID}-{N}.md. Read each receipt file — it contains implementation details, test commands, test output, and files changed. Read the diary and context file for full story context before validating.
```

Wait for completion. Parse per-task verdicts from the batch report.

**For each COMPLETE task**:
1. Update context file: add to "Completed Tasks" section with brief summary
2. Append to diary:
   ```
   ## [{timestamp}] arc-maestro
   [success] Task {N}/{total} batch validated as COMPLETE.
   ---
   ```

**For each INCOMPLETE task**:
1. Revert task in todo file: change `- [x]` back to `- [ ]`
2. Set `failure_counts[task_N] = 1` (batch failure counts as Failure 1)
3. Update state file: write updated `failure_counts`, remove this task from `deferred_tasks`
4. Display: `Task {N} INCOMPLETE after batch validation: {reason}`
5. Apply the **same escalation rules from Step 7.3 E** for "Untagged tasks, difficulty 1-3":
   - Failure 1 (from batch): Retry with `ca-maestro-dev-doer`, include INCOMPLETE reason as context
   - If retry also fails → Failure 2: Escalate to `ca-maestro-senior-dev-doer`
   - If that fails → Failure 3: HALT (present user with options from Step 7.3 E)
6. After each re-implementation, validate per-task with `ca-maestro-task-validator`. On COMPLETE: update context file "Completed Tasks" and update state file (remove failure count entry).

---

### Step 7.5: All Tasks Complete

After all tasks are completed (or skipped):

#### A. Update Context

Edit `.maestro/context-{STORY-ID}.md`:
- **Phase**: Phase 7: Develop
- **Progress**: All tasks completed
- **Last Updated**: {timestamp}
- **Next Action**: Run /arc-maestro-review for code review

#### B. Stage and Commit

Stage all changes and create a commit:

```bash
git add -A
```

Commit with this format:
```
{STORY-ID}: {Story title}

Implemented all tasks:
- {Brief summary of what was built, 2-5 bullet points}

All tests passing. Ready for code review.

Generated with Maestro
Co-Authored-By: Claude <noreply@anthropic.com>
```

#### C. Push

```bash
git push -u origin {branch-name}
```

#### D. Append Final Diary Entry

```
## [{timestamp}] arc-maestro
[success] Phase 7 complete. All {total_tasks} tasks implemented and validated. Changes committed and pushed.
---
```

#### E. Report Completion

Display to user:
```
## Maestro Phase 7 Complete

Story: {STORY-ID} - {title}
Tasks completed: {completed count}/{total count}
{If any skipped: "Tasks skipped: {skipped count}"}
Branch: {branch name}
Commit: {commit hash}

All changes have been committed and pushed.

Next step: Run `/arc-maestro-review` to perform code review and create a PR.
```

---

## Error Handling

### Agent Failures

If a Task tool call for any agent fails unexpectedly (not a validation INCOMPLETE, but an actual agent crash/error):
1. Log the error in the diary with `[problem]` tag
2. Retry once
3. If retry also fails, report to user with error details and ask how to proceed

### Missing Files

If context, diary, or todo files are missing when expected:
- Context file missing -> Cannot proceed. Ask user to start fresh.
- Diary file missing -> Create a new one with a note that previous diary was lost.
- Todo file missing in Phase 7 -> Cannot proceed. Suggest re-running from Phase 4.

### Git Errors

If git operations fail (branch creation, commit, push):
- Display the error to the user
- Do not retry automatically -- git errors often need human judgment
- Suggest resolution steps

---

## Implementation Notes

### Serial Execution

All agent calls are serial -- each task is implemented, validated, then the next begins. No parallel task execution. This ensures each task can build on the work of previous tasks.

### Agent Routing Summary

| Task Type | Agent | Model |
|-----------|-------|-------|
| `[Type: frontend]` (any difficulty) | `ca-maestro-frontend-dev-doer` | Sonnet |
| `[Type: devops]` (any difficulty) | `ca-maestro-devops-dev-doer` | Sonnet |
| Untagged, difficulty 7-10 | `ca-maestro-senior-dev-doer` | Opus |
| Untagged, difficulty 4-6 | `ca-maestro-dev-doer` | Sonnet |
| Untagged, difficulty 1-3 | `ca-maestro-junior-dev-doer` | Haiku |
| Validation: `[Type: frontend]`, difficulty 4+ | `ca-maestro-ui-validator` | Sonnet |
| Validation: difficulty 7+ (per-task) | `ca-maestro-senior-task-validator` | Sonnet |
| Validation: difficulty 4-6 (per-task) | `ca-maestro-task-validator` | Haiku |
| Validation: difficulty 1-3 untagged (batch) | `ca-maestro-batch-validator` | Haiku |

### Escalation Rules

| Task Type | Failure 1 | Failure 2 | Failure 3 |
|-----------|-----------|-----------|-----------|
| `[Type: frontend]` | Retry with frontend specialist | Retry with frontend specialist | HALT |
| `[Type: devops]` | Retry with devops specialist | Retry with devops specialist | HALT |
| Untagged, difficulty 4+ | Retry with same agent | Escalate to senior-dev-doer | HALT |
| Untagged, difficulty 1-3 | Escalate to dev-doer | Escalate to senior-dev-doer | HALT |

### Token Cost Profile

- Phase 2: 1 scout call (Opus) + 1 summary generation (orchestrator) -- heaviest research phase
- Phase 4: 1 planner call (Sonnet)
- Phase 5: 1 reviewer call (Sonnet)
- Phase 7: Per task: 1 dev call + 1 validator call. Difficulty 1-3 untagged: 1 dev call only (batch validates at end). Retries add more calls.
- Phase 7 end: 1 batch validator call (Haiku) covers all deferred tasks at once (if any)
- Total for N tasks, K batched (no retries): 2 + 2(N-K) + K + 1 agent calls

### Tech-Stack Agnostic

This command makes zero assumptions about language, framework, test runner, or cloud provider. All project-specific knowledge comes from the scout's research. Agent prompts never include framework-specific commands.

### Context vs Diary Methodology

- **Context file** (`.maestro/context-{STORY-ID}.md`): Status dashboard. Where things stand RIGHT NOW. Updated by every agent. Uses `<!-- @tag -->` anchors for section queries.
- **Diary file** (`.maestro/diary-{STORY-ID}.md`): Narrative log. HOW we got here. Append-only, chronological. Written when agents discover something non-obvious.
- **Todo file** (`.maestro/todo-{STORY-ID}.md`): Task list with checkboxes, difficulty ratings, and type tags.
- **Summary file** (`.maestro/summary-{STORY-ID}.md`): Condensed research reference (~50 lines) generated by orchestrator after scout. Key patterns, test strategy, citations, constraints. Dev agents read this first; full research in context file.
- **Task receipt files** (`.maestro/task-{STORY-ID}-{N}.md`): Written by ALL dev agents after each task. Contains: what was built, test commands run, test output, files changed. Per-task validators read from this file (not from pasted output). Batch validator reads them for deferred tasks.
- **State file** (`.maestro/state-{STORY-ID}.json`): Persists `current_task_index`, `failure_counts`, `deferred_tasks` after every task. Used by Phase 7 resume to restore loop state without reconstructing from scratch.

### Context File Anchors

The context file uses HTML comment anchors for targeted section extraction:

| Anchor | Section |
|--------|---------|
| `<!-- @story -->` | Story Details (title, type, description, AC) |
| `<!-- @status -->` | Current Status (phase, progress, timestamps) |
| `<!-- @research -->` | Research Findings (scout analysis) |
| `<!-- @tasks -->` | Task Progress (parent section) |
| `<!-- @completed -->` | Completed Tasks (with summaries) |
| `<!-- @current-task -->` | Current Task |
| `<!-- @pending -->` | Pending Tasks |
| `<!-- @outputs -->` | Agent Outputs |
| `<!-- @blockers -->` | Blockers |
| `<!-- @decisions -->` | Decisions |
| `<!-- @review -->` | Code Review Report (added by Phase 8) |

### Diary Entry Format

All diary entries use this format with grep-able tags:
```
## [{timestamp}] {agent-name}
[tag] Description of what happened.
---
```

Tags: `[decision]`, `[problem]`, `[learning]`, `[success]`

---

## Example User Experience

```
User: /arc-maestro PROJ-123

Claude: Maestro initialized for: Add user authentication
        Story ID: PROJ-123
        Source: Jira
        Branch: proj-123-add-user-auth
        Phase 1 complete. Launching scout...

        Phase 2 complete. Scout research done.
        Story type: Full-stack. Found test patterns for .ts, .tsx files.
        2 unanswered questions for user.

        The scout identified 2 questions that need your input:

        1. OAuth provider preference
           Context: Story mentions "social login" but doesn't specify providers.
           Recommendation: Start with Google OAuth, add others later.

        2. Session storage
           Context: No existing session infrastructure found.
           Recommendation: Use JWT tokens (stateless, no session store needed).

User: Use recommendation for both.

Claude: Decisions recorded. Proceeding to planning...

        Phase 4 complete. Plan created with 8 tasks.
        Phase 5 complete. Plan reviewed and improved.

        ## Implementation Plan for PROJ-123
        [Full plan displayed]

        Review the plan above. Approve or request changes?

User: Approved.

Claude: Task 1/8: Create user model and migration
        Routing: ca-maestro-junior-dev-doer (difficulty 3)
        Task 1/8 COMPLETE. Moving to next task...

        Task 2/8: Implement JWT token service
        Routing: ca-maestro-dev-doer (difficulty 5)
        Task 2/8 COMPLETE. Moving to next task...

        Task 3/8: Build OAuth integration
        Routing: ca-maestro-senior-dev-doer (difficulty 7)
        Task 3/8 COMPLETE. Moving to next task...

        Task 4/8: Create login/register UI components
        Routing: ca-maestro-frontend-dev-doer (type: frontend)
        Task 4/8 COMPLETE. Moving to next task...

        [... remaining tasks ...]

        ## Maestro Phase 7 Complete

        Story: PROJ-123 - Add user authentication
        Tasks completed: 8/8
        Branch: proj-123-add-user-auth
        Commit: abc1234

        Next step: Run /arc-maestro-review to perform code review and create a PR.
```

### File-Based Story Example

```
User: /arc-maestro ./stories/my-feature.md

Claude: Maestro initialized for: My Feature Title
        Story ID: FILE-MY-FEATURE
        Source: File: ./stories/my-feature.md
        Branch: file-my-feature-implement-feature
        Phase 1 complete. Launching scout...
        [... continues same flow ...]
```

### Resume Example

```
User: /arc-maestro PROJ-123

Claude: Existing Maestro session found for PROJ-123:
        Phase: Phase 7: Develop
        Progress: Task 5/8 completed
        Next Action: Implement task 6

        Resume from where you left off, or start fresh?

User: Resume.

Claude: Resuming from task 6/8...

        Task 6/8: Add rate limiting middleware
        Routing: ca-maestro-dev-doer (difficulty 4)
        [... continues from where it left off ...]
```
