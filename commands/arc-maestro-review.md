---
description: 🎼🔍 Maestro code review - Phases 8-10 (Code Review, Respond, Complete + PR)
allowed-tools: Read, Write, Bash, Task
argument-hint: [STORY-ID]
---

# Maestro Review 🎼🔍

**Handles Phases 8-10: Code Review → Respond to Concerns → Complete + Create PR**

**IMPORTANT**: This command always starts from Phase 8 (Code Review) when run, unlike `/arc-maestro` which resumes from where it left off.

## Initial Setup

### Step 1: Determine Story ID

**Arguments received**: $ARGUMENTS

1. **IF Story ID provided as argument**:
   - Use the provided story ID (e.g., `PROJ-123` or `FILE-MY-STORY`)
   - Validate format: `[A-Z]+-[A-Z0-9-]+` (supports both Jira IDs like `PROJ-123` and file-based IDs like `FILE-MY-STORY`)

2. **IF no argument provided**:
   - Look for `.maestro-*.md` files in current directory
   - Find the most recently modified one:
     ```bash
     ls -t .maestro-*.md 2>/dev/null | head -1
     ```
   - Extract story ID from filename (e.g., `.maestro-PROJ-123.md` → `PROJ-123` or `.maestro-FILE-MY-STORY.md` → `FILE-MY-STORY`)
   - **IF no .maestro files found**:
     - Say: "⚠️ No Maestro work found in current directory."
     - Say: "Please provide a story ID: `/arc-maestro-review PROJ-123` or `/arc-maestro-review FILE-MY-STORY`"
     - **STOP**

3. **Verify context file exists**:
   - Check if `.maestro-{STORY-ID}.md` exists
   - **IF NOT found**:
     - Say: "⚠️ Context file `.maestro-{STORY-ID}.md` not found."
     - Say: "Run `/arc-maestro {STORY-ID}` first to implement the story."
     - **STOP**

4. **Check current phase and launch code review**:
   - Read `.maestro-{STORY-ID}.md` "Current Status" section
   - Look at the "Phase:" line
   - **IF Phase contains "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5", or "Phase 6"** (development incomplete):
     - Say: "⚠️ Story is still in {Phase}. Complete development first with `/arc-maestro {STORY-ID}`"
     - **STOP**

   - **OTHERWISE** (Phase 7 or later - ready for review):
     - **IF Phase contains "Phase 8", "Phase 9", "Phase 10", "Code Review", or "Complete"**:
       - Say: "♻️ Restarting from Phase 8 - this command always runs fresh code review"
     - **IF Phase contains "Phase 7"**:
       - Say: "📋 Starting Phase 8: Code Review (with bug-finding) for {STORY-ID}..."
     - **IMMEDIATELY launch ca-maestro-code-review agent** (DO NOT skip this step):
       - **IMPORTANT**: Always run the review even if code hasn't changed since last review
       - **Reason**: We may be testing improvements to the review tools themselves
   - Say: "📋 Starting Phase 8: Code Review (with bug-finding) for {STORY-ID}..."
   - Use Task tool with `subagent_type: "ca-maestro-code-review"`
   - Prompt: "Perform comprehensive two-pass code review for story {STORY-ID}. Read guides/bugfinder.md if available for project-specific bug patterns. Generate concerns including bugs with executable failure paths (Pass 1), then vet all concerns using ca-code-review-validator (Pass 2). Separate bugs from code quality concerns. Store the vetted review report in `.maestro-{STORY-ID}.md` and return the complete results."

5. **Review the code review report**:
   - Read the "Code Review" section added to `.maestro-{STORY-ID}.md`
   - Check how many concerns were identified:
     - Bugs (with failure paths)
     - Critical concerns
     - Important concerns
     - Minor suggestions
   - Parse the concern categories

6. **Decision point**:

   **IF no concerns identified:**
   - Say: "✅ Code review complete - no concerns identified!"
   - Update `.maestro-{STORY-ID}.md` Current Status:
     - **Phase**: Phase 10: Complete
     - **Progress**: Code review passed with no concerns
     - **Next Action**: Create pull request
   - Update "Last Updated" timestamp
   - Skip to Phase 10 (step 9)

   **IF concerns identified:**
   - Say: "📋 Code review identified {count} concerns:"
   - Say: "  - 🐛 Bugs: {bug count} (will add regression tests)"
   - Say: "  - 🚨 Critical: {critical count}"
   - Say: "  - ⚠️ Important: {important count}"
   - Say: "  - 💭 Minor: {minor count}"
   - Say: "Launching code review responder to address concerns..."
   - Update `.maestro-{STORY-ID}.md` Current Status:
     - **Phase**: Phase 9: Respond to Concerns
     - **Progress**: Addressing {count} review concerns ({bug count} bugs with regression tests)
     - **Next Action**: Fix, document, or dismiss each concern
   - Proceed to Phase 9

## Phase 9: Respond to Concerns (Enhanced for Bugs)

8. **Launch ca-maestro-code-review-responder agent**:
   - Say: "🔧 Starting Phase 9: Respond to Concerns..."
   - Use Task tool with `subagent_type: "ca-maestro-code-review-responder"`
   - Prompt: "Address all vetted concerns from the code review for story {STORY-ID}. Read the Code Review section in `.maestro-{STORY-ID}.md`. Handle bugs FIRST with regression tests, then address other concerns. For each bug: understand failure path, implement fix, add regression test (if code has test coverage), run tests. For other concerns: decide to fix, document, or dismiss. Implement fixes, run tests, and generate the final completion report."

9. **Receive completion report**:
   - The responder returns the completion report
   - Update `.maestro-{STORY-ID}.md` Current Status:
     - **Phase**: Phase 10: Complete
     - **Progress**: All concerns addressed ({X} bugs fixed with regression tests, {Y} other concerns addressed)
     - **Next Action**: Create pull request
   - Update "Last Updated" timestamp

## Phase 10: Complete + Create PR

10. **Commit any review fixes** (if concerns were addressed):
    - Check if there are uncommitted changes:
      ```bash
      git status --porcelain
      ```
    - **IF changes exist**:
      - Stage all changes: `git add .`
      - Commit:
        ```bash
        git commit -m "$(cat <<'EOF'
        {STORY-ID}: Address code review feedback

        Applied fixes from Maestro code review (Phase 9):
        - Fixed {bug count} bugs with regression tests
        - Addressed {other count} code quality concerns

        All tests passing. Ready for PR.

        🎼 Generated with Maestro - Phase 9: Respond to Concerns
        Co-Authored-By: Claude <noreply@anthropic.com>
        EOF
        )"
        ```
      - Push: `git push`

11. **Create pull request**:
    - Get current branch name: `git branch --show-current`
    - Get story details from `.maestro-{STORY-ID}.md`
    - Create PR using gh CLI:
      ```bash
      gh pr create --title "{STORY-ID}: {Story title}" --body "$(cat <<'EOF'
      ## Summary
      {Brief description of what was implemented}

      ## Changes
      {List of main changes from todo list}

      ## Testing
      - All unit tests passing
      - All integration tests passing
      - Code review: {X} bugs fixed with regression tests, {Y} concerns addressed

      ## Jira
      {STORY-ID}

      🎼 Generated with Maestro
      EOF
      )"
      ```
    - Capture PR URL from output

12. **Final report**:
    - Display the completion report from responder
    - Say: ""
    - Say: "🎉 **Maestro Complete!**"
    - Say: ""
    - Say: "✅ Development: All tasks implemented and validated (Phases 1-7)"
    - Say: "✅ Code Review: {X} bugs + {Y} concerns found and addressed (Phases 8-9)"
    - Say: "✅ Regression Tests: {X} tests added for bug fixes"
    - Say: "✅ Changes: Committed and pushed"
    - Say: "✅ Pull Request: Created (Phase 10)"
    - Say: ""
    - Say: "**Pull Request**: {PR URL}"
    - Say: ""
    - Say: "Ready for team review! 🎼"

### Error Handling

- If `gh` CLI not available, show git commands for manual PR creation
- If not on a feature branch, warn user and ask if they want to continue
- If PR already exists for this branch, show existing PR URL
- If git push fails (e.g., no upstream), show instructions to set upstream

### Important Notes

- This command handles **Phases 8-10** (Enhanced Code Review through Complete + PR)
- **Always starts from Phase 8** - unlike `/arc-maestro`, this command starts from the top each time
- **Bug-finding intelligence**: Code review now checks for tri-state logic, API consistency, framework contracts, edge cases
- **Regression tests**: Bugs get regression tests automatically if code has test coverage
- Can be run with or without story ID argument (supports both Jira IDs like `PROJ-123` and file-based IDs like `FILE-MY-STORY`)
- Automatically detects most recent Maestro work if no ID provided
- Creates PR using branch name and story details
- Commits fixes from code review phase
- Always validates with tests before proceeding
