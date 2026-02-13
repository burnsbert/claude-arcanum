---
description: 🎼 Semi-autonomous development - Launch Maestro for a story
allowed-tools: Read, Write, Bash, mcp__jira__get-issue, mcp__jira-read__get-issue
argument-hint: <JIRA-ID or filepath>
---

# Maestro 🎼 - Semi-Autonomous Development System

**"Orchestrating code, one movement at a time"**

## Phase 1: Initialize

You are starting the Maestro semi-autonomous development system. Your first task is to fetch the story details and create the context file.

### Input Processing

**Arguments received**: $ARGUMENTS

**Your task**:

1. **Determine input type** (Jira ID vs file path):
   - **Check for file path first**:
     - If `$ARGUMENTS` contains `/` OR starts with `./` OR starts with `~` OR ends with `.md` or `.txt`:
       - This is a **file path** - proceed to step 1a (File Path Processing)
     - If `$ARGUMENTS` matches Jira pattern: `[A-Z]+-[0-9]+` (e.g., `PROJ-123`, `TEAM-456`):
       - This is a **Jira ID** - proceed to step 1b (Jira ID Processing)
     - **IF neither**:
       - Say: "⚠️ Maestro requires either a Jira ticket ID or a story file path."
       - Say: "Examples:"
       - Say: "  - Jira ID: `/arc-maestro PROJ-123`"
       - Say: "  - File path: `/arc-maestro ./stories/my-story.md`"
       - Say: "Please provide a Jira ticket ID or file path:"
       - **WAIT for user to provide input**
       - Re-evaluate the provided input

   **1a. File Path Processing**:
   - Expand path if needed (resolve `~` to home directory, `./` to current directory)
   - Check if file exists using the Read tool
   - **IF file does not exist**:
     - Say: "⚠️ File not found: {path}"
     - **WAIT for user to provide valid file path**
   - **IF file exists**:
     - Read the file contents
     - Generate **STORY-ID** from filename:
       - Extract filename without extension (e.g., `my-story.md` → `my-story`)
       - Convert to uppercase kebab-case if needed (e.g., `my story` → `MY-STORY`)
       - Prefix with `FILE-` to distinguish from Jira IDs (e.g., `FILE-MY-STORY`)
     - Set `INPUT_TYPE` = "file"
     - Set `STORY_TEXT` = file contents
     - Set `STORY_SOURCE` = file path
     - Proceed to step 2

   **1b. Jira ID Processing**:
   - Set `INPUT_TYPE` = "jira"
   - Set `STORY-ID` = the Jira ticket ID
   - Proceed to step 2

2. **Ensure correct branch**:
   - Get current branch: `git branch --show-current`
   - Convert STORY-ID to lowercase for branch prefix (e.g., `PROJ-123` → `proj-123`, `FILE-MY-STORY` → `file-my-story`)
   - **IF current branch starts with lowercase STORY-ID** (e.g., `proj-123-feature-name` or `file-my-story-feature`):
     - Say: "✓ Already on branch: {branch name}"
     - Proceed to step 3
   - **IF current branch does NOT start with STORY-ID**:
     - Check if a branch starting with the STORY-ID already exists: `git branch --list "{lowercase-story-id}*"`
     - **IF matching branch exists**:
       - Say: "Found existing branch: {branch name}"
       - Ask user: "Switch to this branch?"
       - **IF yes**: `git checkout {branch name}` and proceed
       - **IF no**: Ask what they want to do
     - **IF no matching branch exists**:
       - Determine base branch (check which exists, prefer in order):
         - `development`
         - `develop`
         - `main`
         - `master`
       - Generate branch name: `{lowercase-story-id}-{succinct-description}`
         - Use lowercase STORY-ID (e.g., `proj-123` or `file-my-story`)
         - Add a brief kebab-case description from the story title (2-4 words)
         - Example: `proj-123-add-csv-export` or `file-my-story-user-auth`
       - Say: "Creating new branch from {base branch}..."
       - Create branch: `git checkout {base branch} && git pull && git checkout -b {branch-name}`
       - Say: "✓ Created branch: {branch-name}"
       - Proceed to step 3

3. **Check for existing work**:
   - Check if `.maestro-{STORY-ID}.md` file exists
   - **IF FILE EXISTS (work in progress)**:
     - Read `.maestro-{STORY-ID}.md`
     - Parse "Current Status" section to get:
       - Current Phase
       - Current Task/Progress within phase
     - Say: "🔄 Found existing Maestro work for {STORY-ID}"
     - Say: "Current status: {Phase} - {Current Task}"
     - Ask user: "Resume from where we left off, or start fresh?"
     - **IF user says resume**:
       - Based on Current Phase, jump to appropriate phase section below
       - **Phase 2-3**: Go to Phase 2
       - **Phase 4-6**: Go to Phase 4
       - **Phase 7**: Go to Phase 7 (development loop)
       - **Phase 8-9**: Go to Phase 8 (code review)
       - **Phase 10**: Go to Phase 10 (complete)
     - **IF user says start fresh**:
       - Delete existing `.maestro-{STORY-ID}.md` and `.maestro-{STORY-ID}-todo.md` files
       - Proceed with step 4 below
   - **IF FILE DOES NOT EXIST**:
     - Proceed with step 4 below (initialization)

4. **Get story details** (based on INPUT_TYPE):

   **IF INPUT_TYPE = "jira"**:
   - Use available Jira MCP tools to fetch the complete ticket details
   - Available MCP tools (try in order, use whichever is available):
     - `mcp__jira__get-issue` (standard Jira MCP)
     - `mcp__jira-read__get-issue` (read-only Jira MCP)
   - Extract:
     - Title/Summary
     - Description
     - Acceptance Criteria (if present)
     - Issue Type (Story, Bug, Task, etc.)
     - Status
     - Priority
     - Any other relevant fields

   **IF INPUT_TYPE = "file"**:
   - Story text was already loaded in step 1a (STORY_TEXT variable)
   - Parse the story text to extract (if present in the file):
     - Title/Summary (first heading or first line)
     - Description (main body text)
     - Acceptance Criteria (section labeled "Acceptance Criteria" or "AC" if present)
     - Type (default to "Story" unless specified in file)
   - Note: File-based stories may be less structured - extract what's available

5. **Create `.maestro-{STORY-ID}.md` file**:
   - Use the STORY-ID as filename (e.g., `.maestro-PROJ-123.md` or `.maestro-FILE-MY-STORY.md`)
   - File structure:

```markdown
# Maestro Context: {STORY-ID}

## Story Details
**Source**: {Jira: STORY-ID | File: filepath}
**Title**: {story title}
**Type**: {Story/Bug/Task}
**Priority**: {priority if available, or "Not specified" for file-based}
**Status**: {status if available, or "Not specified" for file-based}

**Description**:
{full story description}

**Acceptance Criteria**:
{acceptance criteria if available}

## Current Status
**Phase**: Phase 1: Initialize
**Progress**: Story initialized, loading details
**Started**: {current timestamp}
**Last Updated**: {current timestamp}
**Next Action**: Launch scout agent for research

_Phase tracking: Agents should update Phase, Progress, Last Updated, and Next Action as work progresses_

## Research Findings
_Research will be added here by research agents_

## Task Progress

### Completed Tasks
_Track completed tasks here as development progresses_

### Current Task
_Track the task currently being worked on_

### Pending Tasks
_Remaining tasks from the plan_

## Agent Outputs
_Agent outputs will be recorded here_

## Blockers
_None at initialization_

## Decisions
_Key decisions will be recorded here_
```

6. **Report initialization to user**:
   - Confirm story details loaded
   - Show the file path created
   - Display a brief summary of the story
   - Say: "Story initialized. Launching scout agent for research..."

## Phase 2: Scout Research

7. **Launch ca-maestro-scout agent**:
   - Use the Task tool with `subagent_type: "ca-maestro-scout"`
   - Provide the story details and point it to `.maestro-{STORY-ID}.md`
   - Prompt: "Research the codebase for story {STORY-ID}. The story details are in `.maestro-{STORY-ID}.md`. Analyze the story, generate implementation questions, research the codebase thoroughly, and update the Research Findings section of the context file with your complete report."

8. **Review scout's findings**:
   - Read the updated `.maestro-{STORY-ID}.md` Research Findings section
   - Check for "Unanswered Questions" section in the scout's report
   - Check for "Story Gaps Requiring Clarification" section

## Phase 3: Questions (if needed)

9. **Decision point**:

   **IF scout has unanswered questions or story gaps:**
   - Display the questions/gaps clearly to the user
   - Say: "The scout identified some questions that need answers before planning:"
   - List each question with context
   - Ask user: "Please provide answers to these questions so we can proceed with planning."
   - **WAIT for user response**
   - Record user's answers in `.maestro-{STORY-ID}.md` under "Decisions" section
   - Update "Last Updated" timestamp

   **IF scout has NO open questions:**
   - Say: "Scout research complete! I have everything I need to plan."
   - Proceed immediately to Phase 4

## Phase 4: Plan

10. **Launch ca-maestro-planner agent**:
    - Use the Task tool with `subagent_type: "ca-maestro-planner"`
    - Provide the ticket ID
    - Prompt: "Create detailed implementation plan for story {STORY-ID}. Read all research findings from `.maestro-{STORY-ID}.md` and create a comprehensive task breakdown in `.maestro-{STORY-ID}-todo.md`. Follow TDD practices, avoid code duplication, and leverage patterns found by the scout."

11. **Read the generated plan**:
    - Read `.maestro-{STORY-ID}-todo.md`
    - Parse the task breakdown

## Phase 5: Review (Quality Gate)

12. **Launch ca-maestro-plan-reviewer agent**:
    - Use the Task tool with `subagent_type: "ca-maestro-plan-reviewer"`
    - Provide the ticket ID
    - Prompt: "Review the implementation plan for story {STORY-ID}. Vet the scout's research in `.maestro-{STORY-ID}.md`, the user's answers, and the planner's task breakdown in `.maestro-{STORY-ID}-todo.md`. Identify problems, gaps, and opportunities for improvement. Apply ALL improvements directly to the plan - the user will review it next."

14. **Plan has been improved**:
    - The reviewer has automatically applied all improvements BEFORE user review
    - User will see the polished, improved version of the plan
    - Read the updated `.maestro-{STORY-ID}-todo.md` (now improved)
    - Read the Plan Review section in `.maestro-{STORY-ID}.md` (shows what was changed)
    - Proceed to Phase 6

## Phase 6: Approve

15. **Present plan to user**:
    - Say: "Plan has been reviewed and improved by the plan-reviewer."
    - Display the complete plan clearly
    - Show task count and organization
    - Say: "Here's the implementation plan:"
    - [Show the plan]
    - Ask: "Do you approve this plan, or would you like to make changes?"

16. **Handle user response**:

    **IF user approves:**
    - Say: "Plan approved! Starting implementation..."
    - Update `.maestro-{STORY-ID}.md` Current Status:
      - **Phase**: Phase 7: Develop
      - **Progress**: Plan approved, starting task-by-task implementation
      - **Next Action**: Implement first task
    - Proceed to Phase 7

    **IF user requests changes:**
    - Note the requested changes
    - Update the `.maestro-{STORY-ID}-todo.md` file with the changes
    - Regenerate/revise the plan based on feedback
    - Show revised plan and ask again
    - Continue loop until plan is approved

## Phase 7: Develop (Task by Task)

### ⛔ MANDATORY VALIDATION RULE ⛔

**THE FOLLOWING SEQUENCE IS REQUIRED FOR EVERY SINGLE TASK:**

```
1. dev-doer implements task
2. VALIDATOR RUNS (non-negotiable)
3. Only AFTER validator says COMPLETE can you proceed
```

**VIOLATIONS THAT ARE NOT ALLOWED:**
- ❌ Marking a task complete without running validator
- ❌ Moving to next task without validator confirmation
- ❌ Assuming dev-doer's "tests pass" claim is sufficient
- ❌ Skipping validator "because the task looks done"
- ❌ Running dev-doer twice in a row without validator between them

**If you find yourself about to launch dev-doer for task N+1, STOP and ask: "Did I run the validator for task N?" If no, GO BACK and run the validator.**

---

17. **Initialize development tracking**:
    - Read `.maestro-{STORY-ID}-todo.md` to get all tasks
    - Track current task and failure count per task
    - Set failure limit: 3 attempts per task

18. **For each task in the todo list** (repeat steps A-F for EVERY task):

    **A. Parse task type and difficulty, then select agent**:
    - **FIRST**: Check for specialist type tag: look for `[Type: frontend]` or `[Type: devops]` in task description
    - **THEN**: Extract difficulty rating: look for `[Difficulty: N/10]` in task description
    - **Routing priority** (check in this order):
      1. **If `[Type: frontend]`**: Use `ca-maestro-frontend-dev-doer` (Opus) - regardless of difficulty
      2. **If `[Type: devops]`**: Use `ca-maestro-devops-dev-doer` (Opus) - regardless of difficulty
      3. **If no type tag AND difficulty >= 7**: Use `ca-maestro-senior-dev-doer` (Opus)
      4. **If no type tag AND difficulty < 7**: Use `ca-maestro-dev-doer` (Sonnet)
      5. **If no type tag AND no difficulty found**: Default to `ca-maestro-dev-doer`

    **B. Launch appropriate dev-doer agent**:
    - **For `[Type: frontend]` tasks**:
      - Use Task tool with `subagent_type: "ca-maestro-frontend-dev-doer"`
      - Say: "🎨 Frontend task - routing to frontend specialist (Opus)"
      - Prompt: "Implement this FRONTEND task: {task description}. Read all context from `.maestro-{STORY-ID}.md`. Apply frontend expertise - component architecture, accessibility, responsive design. Follow patterns from scout research. Ensure all tests pass. This is task {N} of {total}."
    - **For `[Type: devops]` tasks**:
      - Use Task tool with `subagent_type: "ca-maestro-devops-dev-doer"`
      - Say: "🏗️ DevOps/infra task - routing to DevOps specialist (Opus)"
      - Prompt: "Implement this DEVOPS/INFRASTRUCTURE task: {task description}. Read all context from `.maestro-{STORY-ID}.md`. Apply infrastructure expertise - AWS services, security, IaC best practices. Follow patterns from scout research. Ensure all tests/validation pass. This is task {N} of {total}."
    - **For untagged difficulty 1-6**:
      - Use Task tool with `subagent_type: "ca-maestro-dev-doer"`
      - Prompt: "Implement this task: {task description}. Read all context from `.maestro-{STORY-ID}.md`. Follow patterns from scout research. Update tests. Ensure all tests pass. This is task {N} of {total}."
    - **For untagged difficulty 7-10**:
      - Use Task tool with `subagent_type: "ca-maestro-senior-dev-doer"`
      - Say: "🔥 High difficulty task (7+/10) - routing to senior dev-doer (Opus)"
      - Prompt: "Implement this HIGH DIFFICULTY task: {task description}. Difficulty: {N}/10. Read all context from `.maestro-{STORY-ID}.md`. This task requires careful analysis and implementation. Follow patterns from scout research. Handle edge cases thoroughly. Ensure all tests pass. This is task {N} of {total}."

    **C. Review dev-doer's work**:
    - Read the implementation summary from dev-doer
    - Note what was implemented and test results

    ---
    ### ⛔ STOP - MANDATORY VALIDATION CHECKPOINT ⛔
    **You MUST complete step D before proceeding. No exceptions.**
    ---

    **D. Launch ca-maestro-task-validator** ⚠️ **MANDATORY - NEVER SKIP**:
    - Say: "🔍 Running validator for Task {N}..."
    - Use Task tool with `subagent_type: "ca-maestro-task-validator"`
    - Provide: Task description, dev-doer's summary, ticket ID
    - Prompt: "Validate that this task is TRULY complete: {task description}. Review the implementation summary and verify: full scope implemented, all tests pass (no skips/failures), no shortcuts taken. Return STATUS: COMPLETE or INCOMPLETE with reasons."
    - **WAIT for validator response before proceeding to step E**

    **E. Review validator's assessment**:
    - Read the validation result
    - Check status: COMPLETE or INCOMPLETE
    - **You MUST have a validator response to proceed**

    **F. Handle validation outcome**:

    **IF COMPLETE:**
    - Mark task as complete in `.maestro-{STORY-ID}-todo.md`
    - Update `.maestro-{STORY-ID}.md` Task Progress section:
      - Move task from "Current Task" to "Completed Tasks" with summary
      - Include: task number, description, files changed, key accomplishments
      - Example:
        ```markdown
        ### Completed Tasks
        1. ✅ Create Migration Script (Task 1/19)
           - Created: application/migrations/20250118_add_feature.php
           - Action: Executed migration on both database shards
           - Status: Migration successful, tables updated
        ```
    - Reset failure count for this task
    - Say: "✅ Task {N} complete: {task description}"
    - Move to next task

    **IF INCOMPLETE:**
    - Increment failure count for this task
    - IF failure count < 3:
      - **Check if escalation to senior is appropriate:**
        - If task has `[Type: frontend]` or `[Type: devops]` (specialist task):
          - Specialist tasks do NOT escalate to a different agent - retry with the same specialist
          - Say: "Task {N} incomplete (attempt {count}/3). Retrying with same specialist. Issues: {validator reasons}"
        - Else if task was using `ca-maestro-dev-doer` (not already senior) AND failure count = 2:
          - Say: "⚡ Escalating to senior dev-doer (Opus) after 2 failed attempts"
          - Set flag to use `ca-maestro-senior-dev-doer` for attempt 3
          - Include failure context in prompt: "Previous attempts failed due to: {validator reasons}. This is an escalation - apply deeper analysis."
        - Otherwise (already using senior OR failure count = 1):
          - Say: "Task {N} incomplete (attempt {count}/3). Issues: {validator reasons}"
      - Retry task (with senior if escalated, specialist if specialist, otherwise same agent)
    - IF failure count = 3:
      - **HALT DEVELOPMENT**
      - Say: "⚠️ Stuck on task {N} after 3 attempts. Issues: {validator reasons}"
      - Update `.maestro-{STORY-ID}.md` Current Status:
        - **Phase**: Phase 7: Develop (Blocked)
        - **Progress**: Stuck on task {N} after 3 attempts
        - **Next Action**: User decision required
      - Document blocker in context file
      - Ask user: "This task has failed 3 times. Options: 1) You implement it manually, 2) Adjust task scope, 3) Skip and continue"
      - **WAIT for user decision**

19. **After all tasks complete**:
    - Say: "🎉 All tasks implemented and validated!"
    - Update `.maestro-{STORY-ID}.md` Current Status:
      - **Phase**: Phase 7: Develop (Complete)
      - **Progress**: All tasks implemented and validated
      - **Next Action**: Ready for code review (use /arc-maestro-review)
    - Update "Last Updated" timestamp

20. **Commit and push changes**:
    - Stage all changes: `git add .`
    - Create commit with message from story:
      ```bash
      git commit -m "$(cat <<'EOF'
      {STORY-ID}: {Story title}

      Implemented all tasks:
      - {Brief summary of what was done}

      All tests passing. Ready for code review.

      🎼 Generated with Maestro
      Co-Authored-By: Claude <noreply@anthropic.com>
      EOF
      )"
      ```
    - Push to remote: `git push`

21. **Report completion**:
    - Say: "✅ Development complete for {STORY-ID}!"
    - Say: "All changes committed and pushed to remote."
    - Say: ""
    - Say: "**Next Steps:**"
    - Say: "Run `/arc-maestro-review {STORY-ID}` to:"
    - Say: "  • Perform two-pass code review"
    - Say: "  • Address any concerns"
    - Say: "  • Create pull request"
    - Say: ""
    - Say: "Or review the changes yourself first, then run `/arc-maestro-review` when ready."

---

**End of /arc-maestro command. Use /arc-maestro-review for Phase 8-10 (Code Review, Respond, Complete)**

---

### Error Handling

- **For Jira-based stories**:
  - If Jira MCP tools are not available, suggest using a file-based story instead
  - If the ticket ID doesn't exist, report the error and ask user to verify the ticket ID
- **For file-based stories**:
  - If file path doesn't exist, report the error and ask for a valid path
  - If file is empty or unreadable, report the error
- If the `.maestro-{STORY-ID}.md` file already exists, ask the user if they want to:
  - Continue with existing context
  - Reset and start fresh
  - Cancel

### Important Notes

- This command handles **Phases 1-7** (Initialize through Develop):
  - **Phase 1 Initialize**: Fetch story, create context files
  - **Phase 2 Scout**: Research codebase
  - **Phase 3 Questions**: User clarifies ambiguities if needed
  - **Phase 4 Plan**: Create TDD task breakdown
  - **Phase 5 Review**: Improve plan (quality gate)
  - **Phase 6 Approve**: User approves plan
  - **Phase 7 Develop**: Implement and validate tasks
- When complete, commits and pushes changes
- Use `/arc-maestro-review {STORY-ID}` for Phases 8-10 (Code Review, Respond, Complete + PR)
- User checkpoints: Questions, plan approval, blockers
- All state in `.maestro-{STORY-ID}.md` and `.maestro-{STORY-ID}-todo.md`
- Tasks cannot be skipped - validator enforces completion
- Development halts after 3 failures on same task
