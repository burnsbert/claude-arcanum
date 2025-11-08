# Root Cause Analysis (RCA)

This is a top-level user command that invokes the arc-root-cause-analyzer agent to perform forensic analysis on a bug. Works with bugs that were just fixed or are currently being worked on.

## Instructions

This command extracts context from the current session and invokes the arc-root-cause-analyzer agent with the appropriate information.

### Usage Scenarios

**Scenario 1: Just fixed a bug**
```
User: /arc-rca
```
Claude extracts from the current session:
- What bug was fixed
- What files were modified
- What commits were made
- How the bug manifested

**Scenario 2: Working on an unfixed bug**
```
User: /arc-rca
```
Claude extracts from the current session:
- What bug is being investigated
- What files are involved
- What the symptoms are
- What's been discovered so far

**Scenario 3: Analyze a specific bug**
```
User: /arc-rca "authentication tokens expiring immediately, fixed in commit abc123"
User: /arc-rca bug-id: JIRA-1234
User: /arc-rca commit abc123
```
Claude uses the provided information to focus the analysis.

### Command Execution Steps

1. **Extract Context from Session or Parameters**

   If parameter provided:
   - Use the parameter as the bug description/identifier
   - If it looks like a commit hash, use that as the fix commit
   - If it looks like a bug ID, treat it as reference
   - Otherwise treat as bug description

   If no parameter:
   - Analyze the conversation history to determine:
     - What bug has been discussed/worked on
     - Whether it's been fixed (look for commits, file changes)
     - What files/components are involved
     - What the symptoms were/are
     - What commits were made (if fixed)
     - What's known about the cause

2. **Determine Bug Status**

   **Fixed Bug Indicators**:
   - Recent commits were made in this session
   - User said "fixed", "solved", "resolved"
   - Changes were made to address an issue
   - Tests are now passing after changes

   **Unfixed Bug Indicators**:
   - Still investigating
   - Tests are still failing
   - No commits made yet
   - User is stuck on the problem

3. **Gather Required Information for Agent**

   **For Fixed Bugs**:
   - Bug description and symptoms
   - Files that were modified
   - Commit hash(es) that fixed it (from git log or conversation)
   - What the fix changed (git diff or from Edit tool usage)

   **For Unfixed Bugs**:
   - Bug description and symptoms
   - Files/components involved
   - What's known about the cause (if anything)
   - Current investigation status

4. **Invoke the arc-root-cause-analyzer Agent**

   Use the Task tool to launch the agent with:
   ```
   Please analyze the root cause of this bug:

   Bug Description: [extracted or provided]
   Status: [Fixed / Unfixed]

   [For fixed bugs]
   Fix Commit(s): [commit hashes]
   Files Modified: [list of files]
   What Was Changed: [summary of changes]

   [For unfixed bugs]
   Affected Files: [list]
   Known Cause: [what we know so far, or "under investigation"]
   Symptoms: [how it manifests]

   Please provide a comprehensive root cause analysis including:
   - Commit hash that introduced the bug
   - Date/time of that commit
   - Author of that commit
   - Full root cause analysis with prevention recommendations
   ```

   **Note**: The agent will automatically use git commands to extract commit, date,
   and author information for the breaking change. This is ALWAYS included in the
   analysis report.

5. **Present Results**

   After the agent completes, present the results to the user and ask:
   ```
   Root cause analysis complete.

   [Summary of key findings from agent]

   Would you like to:
   1. See the full detailed report
   2. Investigate similar risks in the codebase
   3. Create prevention tasks based on recommendations
   4. Export analysis for documentation
   5. Something else
   ```

## Context Extraction Guidelines

### From Recent Session Activity

**Look for**:
- File edits (Edit tool usage)
- Git commands (commits, diffs, logs)
- Error messages discussed
- Test runs and results
- User descriptions of the problem

**Extract**:
- **Bug description**: What was wrong? What were the symptoms?
- **Fixed or unfixed**: Did we commit a fix?
- **Files involved**: Which files were read, edited, or discussed?
- **Fix details**: What changed? (from Edit calls or git diff)
- **Timeline**: When did we start working on this? When was it fixed?

### Identifying Fix Commits

Check for:
- Bash commands like `git commit -m "..."`
- User mentioning "committed", "pushed"
- Git log output in the conversation
- Successful test runs after changes

Extract the commit hash from:
- Git command output
- User providing it explicitly
- Most recent commit if just made

### Handling Insufficient Context

If the session context doesn't provide enough information:

```
I need more information to perform a root cause analysis.

What I found in our session:
- [What was found]

What's missing:
- [What's needed]

Please provide:
- Bug description and symptoms
- Whether it's fixed (and if so, the commit hash)
- Which files/components are affected

Or you can run: /arc-rca "your bug description here"
```

## Examples

### Example 1: Just Fixed Bug

```
[Session context: User was debugging token expiration issue, made edits to
tokenService.ts, ran tests, committed with message "Fix token expiration"]

User: /arc-rca

Claude: I'll analyze the root cause of the token expiration bug you just fixed.

[Extracts from session]:
- Bug: Tokens expiring immediately instead of 24 hours
- Status: Fixed in commit abc123def
- Files: src/auth/tokenService.ts
- Fix: Changed expiresIn calculation

[Invokes arc-root-cause-analyzer agent]

Agent: [Performs full root cause analysis...]

Claude: Root cause analysis complete.

Key Findings:
- Bug introduced during time constant refactoring on 2024-12-15
- Root cause: Units mismatch (milliseconds vs seconds)
- Fix quality: Complete but similar bug found in redis.ts
- Prevention: Need integration tests and unit documentation

Would you like to:
1. See the full detailed report
2. Fix the similar bug in redis.ts
3. Create tasks for prevention recommendations
```

### Example 2: Unfixed Bug

```
[Session context: User investigating rendering issue in UserProfile, no fix yet]

User: /arc-rca

Claude: I'll analyze the root cause of the rendering issue in UserProfile.

[Extracts from session]:
- Bug: UserProfile component not re-rendering on state change
- Status: Unfixed - still investigating
- Files: src/components/UserProfile.tsx, src/hooks/useUserData.ts
- Known: State updates happening but component doesn't reflect them

[Invokes arc-root-cause-analyzer agent]

Agent: [Performs investigation...]

Note: Insufficient information for complete root cause analysis at this stage.
However, investigation suggests:
- Likely introduced in recent refactor (commit def456)
- Possible state mutation issue at UserProfile.tsx:45
- Recommend fixing the bug first, then re-run /arc-rca for full analysis

Claude: The agent found likely causes but recommends fixing the bug first
for a complete analysis. Based on investigation:

Likely introduced: commit def456 (refactor to functional components)
Suspected issue: Direct state mutation at line 45

Would you like to:
1. Fix the suspected issue and re-run analysis
2. See investigation details
3. Use /arc-investigate for systematic troubleshooting
```

### Example 3: With Parameter

```
User: /arc-rca "auth bug fixed in commit abc123"

Claude: I'll analyze that bug.

[Looks up commit abc123]
[Extracts changes and context]
[Invokes arc-root-cause-analyzer agent]

[Agent performs analysis...]

Claude: Root cause analysis complete for authentication bug.

[Presents findings...]
```

## Important Notes

- **Don't ask unnecessary questions** - Extract from context when possible
- **Be intelligent about status** - If commits were made, bug is likely fixed
- **Provide context to agent** - Give the agent all relevant information
- **Handle edge cases gracefully** - If insufficient info, explain what's missing
- **Make it seamless** - User should just type `/arc-rca` and get results

## Command Behavior

```
Input: /arc-rca [optional: bug description/commit/id]

Process:
1. Extract context from session or use parameter
2. Determine bug status (fixed/unfixed)
3. Gather required information
4. Invoke arc-root-cause-analyzer agent
5. Present results with action options

Output: Root cause analysis with key findings and next steps
```

This command makes root cause analysis as simple as typing `/arc-rca` - the rest happens automatically.
