---
description: Analyze PR review feedback with validation and provide prioritized response plan
allowed-tools: "*"
---

# Arc PR Respond - Validated Feedback Analysis

Parse, validate, and prioritize feedback from a reviewed GitHub PR: {{args}}

This command performs a two-pass analysis:
1. **Pass 1**: Fetch and categorize all feedback
2. **Pass 2**: Validate complex/uncertain items using ca-code-review-validator
3. **Synthesis**: Present finalized assessments with recommended priorities

---

## PREREQUISITE: Check for GitHub CLI

Check if `gh` is installed: `gh --version`

**If not found**, auto-install by detecting platform:

- **macOS**: `brew install gh` (if Homebrew available)
- **Linux**: `apt-get install gh` (Ubuntu/Debian) or `dnf install gh` (Fedora) or `pacman -S github-cli` (Arch)
- **Windows**: `winget install GitHub.cli` (Windows 11/10) or `choco install gh` (Chocolatey) or `scoop install gh` (Scoop)

After install: `gh auth login`

If auto-install unavailable: https://cli.github.com

---

## PASS 1: Fetch and Categorize Feedback

### Step 1.1: Fetch All PR Feedback

**CRITICAL**: You MUST fetch ALL three types of comments separately:

1. **General PR reviews**: `gh pr view <number> --json reviews,comments`
2. **Inline code comments**: `gh api repos/{owner}/{repo}/pulls/{number}/comments`
3. **Issue comments**: `gh api repos/{owner}/{repo}/issues/{number}/comments`

Parse the PR URL to extract owner, repo, and number for API calls.

**DO NOT** rely only on `gh pr view` - it may not include all inline comments.

### Step 1.2: Parse Reviewer Arguments

From `{{args}}`:
- Extract PR URL/number
- Extract reviewer filter if specified:
  - `humans` - Exclude all bot comments (CodeRabbit, github-actions, etc.)
  - `<name>` - Only include feedback from specific reviewer(s)
  - Default - Include all feedback including bots

Examples:
- `/arc-pr-respond https://github.com/owner/repo/pull/123` - All feedback
- `/arc-pr-respond 123 humans` - Only human reviewers
- `/arc-pr-respond 123 brian` - Only Brian's feedback
- `/arc-pr-respond 123 michael brian` - Michael and Brian's feedback

### Step 1.3: Initial Categorization

For each feedback item, create an initial assessment:

```markdown
## Pass 1: Initial Categorization

**Item ID**: [Letter+Number, e.g., A1, A2, B1, B2]
**Reviewer**: [Name]
**Location**: [file:line or "General comment"]
**Feedback**: [Full feedback text]

**Initial Category**:
- [ ] Question - Reviewer asking for clarification
- [ ] Bug Report - Reviewer identified potential bug
- [ ] Suggestion - Improvement or alternative approach proposed
- [ ] Praise - Positive feedback
- [ ] Style/Formatting - Code style or formatting preference
- [ ] Documentation - Missing or incorrect documentation
- [ ] Testing - Missing or inadequate tests
- [ ] Performance - Performance concern
- [ ] Security - Security vulnerability or concern

**Complexity**:
- [ ] Simple - Obvious issue or straightforward question (typo, clear bug, simple question)
- [ ] Moderate - Involves judgment or trade-offs
- [ ] Complex - Requires deep analysis or has unclear validity

**Initial Validity Assessment**:
- [ ] Clearly Valid - Obvious issue or good suggestion
- [ ] Clearly Invalid - Based on misunderstanding or incorrect assumption
- [ ] Uncertain - Needs deeper analysis to assess
```

### Step 1.4: Identify Items Needing Validation

Review all categorized items and mark which need validation:

**MUST VALIDATE** (these warrant ca-code-review-validator assessment):
- Complexity is Moderate or Complex
- Initial Validity is Uncertain
- Category is Suggestion with trade-offs
- Category is Performance or Security (need to verify severity)
- Architectural feedback or design decisions
- Feedback that contradicts your understanding

**DO NOT VALIDATE** (these are obvious - skip to save time):
- Complexity is Simple AND Initial Validity is Clearly Valid
  - Examples: Typo fixes, obvious bugs, clear questions, missing semicolons
- Complexity is Simple AND Initial Validity is Clearly Invalid
  - Examples: Feedback based on clear misunderstanding of code
- Category is Praise (no action needed)
- Style/Formatting that's clearly subjective (just acknowledge)

Create a list:
```markdown
## Items for Validation (Pass 2)
- A1, A3, A5, B2, B4 [5 items total]

## Items Not Needing Validation (Already Clear)
- A2 (typo fix), A4 (clear question), B1 (praise), B3 (obvious bug)
```

---

## PASS 2: Validate Complex Feedback

### Step 2.1: Run Validation for Each Item

For each feedback item identified in Step 1.4, invoke ca-code-review-validator agent:

**Use the Task tool** for each item:

```
Review the following code review feedback received on my PR:

File: [file:line from feedback]
Feedback: "[Complete feedback text]"

Context: I'm the PR author. This is feedback I received. Is this feedback:
- Correct and should be addressed?
- Has merit but involves trade-offs?
- Based on misunderstanding?
- A nitpick/minor preference?

My PR is attempting to: [brief description of PR goal]
```

**Run validators in parallel** - if you have 5 items to validate, send one message with 5 Task tool invocations.

### Step 2.2: Collect Validation Results

For each validated item, ca-code-review-validator will return:
- **Verdict**: ✅ FULLY ENDORSE / ⚠️ ENDORSE WITH CAVEATS / ❌ DISAGREE / 🔵 MINOR/NITPICK / 🤔 DEPENDS/CLARIFY / 🎯 OUT OF SCOPE
- **Reasoning**: Evidence-based assessment
- **Recommendation**: What to do about it

Collect all results before proceeding to synthesis.

---

## SYNTHESIS: Finalized Feedback Analysis

### Step 3.1: Synthesize Each Feedback Item

For each feedback item (both validated and non-validated), create final assessment:

**Format** (use bold headers with separator lines for visibility):

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**A1. [Reviewer Name] - [Brief summary of feedback point]**

**Location**: `file:line` (or "General comment")

**Feedback**:
[Full feedback text from reviewer]

**Assessment**: [✅ Valid / ⚠️ Partially Valid / ❌ Invalid / 🔵 Minor/Nitpick / 💬 Question]

**Reasoning**:
[Your assessment with validator insights if validated]
[If validated: Note key points from ca-code-review-validator]

**Priority**: [🔴 High / 🟡 Medium / 🟢 Low / ⚪ No Action]

**Recommended Response**:
[Draft response to reviewer]

**Recommended Action**:
[What you should actually do: Fix the code / Add comment / Clarify in response / Acknowledge / No change needed]
```

#### Assessment Categories:

- **✅ Valid**: Feedback is correct and should be addressed
  - Use for: Actual bugs, missing tests, real security issues, good suggestions

- **⚠️ Partially Valid**: Has merit but involves trade-offs or context
  - Use for: Suggestions with pros/cons, subjective improvements, context-dependent issues

- **❌ Invalid**: Based on misunderstanding or incorrect assumptions
  - Use for: Feedback that's factually wrong or misunderstands the code

- **🔵 Minor/Nitpick**: Technically correct but very minor
  - Use for: Style preferences, naming suggestions, minor formatting

- **💬 Question**: Reviewer asking for information/clarification
  - Use for: All questions (separate from validity assessment)

#### Priority Levels:

- **🔴 High**: Must address before merge (security, bugs, breaking changes, critical tests)
- **🟡 Medium**: Should address (good suggestions, moderate issues, important questions)
- **🟢 Low**: Nice to have (minor improvements, style tweaks, low-impact suggestions)
- **⚪ No Action**: Acknowledge but don't change (invalid feedback, out-of-scope, already handled)

### Step 3.2: Synthesis Guidelines

**For items NOT validated** (simple/obvious):
- Provide your own straightforward assessment
- Example: "Valid - This is a typo that should be fixed"
- Example: "Invalid - This code path is actually tested in integration-test.js:45"

**For items validated as ✅ FULLY ENDORSE**:
- Assessment: ✅ Valid
- Priority: Usually 🔴 High or 🟡 Medium
- Include validator's key reasoning if it adds value
- Example note: "(Validator confirmed: This could cause data corruption)"

**For items validated as ⚠️ ENDORSE WITH CAVEATS**:
- Assessment: ⚠️ Partially Valid
- Priority: Usually 🟡 Medium or 🟢 Low
- Include validator's trade-offs analysis
- Example note: "(Trade-off: Improves readability but adds 10ms latency)"

**For items validated as ❌ DISAGREE**:
- Assessment: ❌ Invalid
- Priority: ⚪ No Action
- Include validator's reasoning why feedback is incorrect
- Draft response explaining the misunderstanding politely

**For items validated as 🔵 MINOR/NITPICK**:
- Assessment: 🔵 Minor/Nitpick
- Priority: 🟢 Low or ⚪ No Action
- Note it's subjective/low priority
- Keep response brief

**For items validated as 🤔 DEPENDS/CLARIFY**:
- Assessment: 💬 Question (treat as question needing more context)
- Priority: 🟡 Medium (need to clarify)
- Draft response asking for clarification based on validator's questions

---

## FINAL OUTPUT: Complete Feedback Analysis

### Output Format:

```markdown
# PR Feedback Analysis: [PR Title]

## 📊 Overview

**Total Feedback Items**: [N]
**By Reviewer**:
- [Reviewer A]: [count] items
- [Reviewer B]: [count] items

**By Priority**:
- 🔴 High: [count] items
- 🟡 Medium: [count] items
- 🟢 Low: [count] items
- ⚪ No Action: [count] items

**Validated Items**: [count] items were validated using ca-code-review-validator

---

## 📋 Detailed Feedback Analysis

[For each feedback item, use the format from Step 3.1 above]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**A1. [Reviewer] - [Summary]**
[Full analysis as specified above]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**A2. [Reviewer] - [Summary]**
[Full analysis...]

---

## 🎯 Recommended Action Plan

### Priority 1: Address Before Merge (🔴 High Priority)

1. **[Item ID]** - [Brief description]
   - **What to do**: [Specific action]
   - **File**: [file:line if applicable]

2. **[Item ID]** - [Brief description]
   - **What to do**: [Specific action]
   - **File**: [file:line if applicable]

### Priority 2: Should Address (🟡 Medium Priority)

1. **[Item ID]** - [Brief description]
   - **What to do**: [Specific action]

### Priority 3: Nice to Have (🟢 Low Priority)

1. **[Item ID]** - [Brief description]
   - **What to do**: [Specific action]

### Responses Only (⚪ No Code Changes)

1. **[Item ID]** - [Brief description]
   - **What to do**: Post response to explain/acknowledge

---

## 💬 Draft Responses Ready to Post

[For items needing responses, provide copy-pasteable responses]

**Response to Item A1**:
```
[Draft response text that can be copied directly to GitHub]
```

**Response to Item A3**:
```
[Draft response text]
```

---

## ✅ Quick Checklist

Before responding:
- [ ] All 🔴 High Priority items have action plans
- [ ] All questions (💬) have responses drafted
- [ ] Invalid feedback (❌) has polite explanations prepared
- [ ] Trade-offs noted for ⚠️ Partially Valid items

---

## 📝 Summary

[2-3 paragraph summary including:]
- Overall quality of feedback received
- Key themes (security, testing, performance, style)
- Major items to address
- Any feedback that was validated and what validator found
- Estimated effort to address all feedback
```

---

## Important Notes

### Efficiency Considerations
- **Selective validation**: Only validate 20-40% of items (complex/uncertain ones)
- **Parallel validation**: Run all validators in parallel with single message
- **Skip obvious items**: Don't waste time validating typos or clear bugs

### Response Tone
- **Professional and appreciative**: Thank reviewers for their time
- **Clear explanations**: When disagreeing, explain why politely
- **Acknowledge trade-offs**: For partially valid feedback, note what you're choosing and why
- **Ask questions**: When unclear, ask for clarification rather than assuming

### Validator Usage
The ca-code-review-validator provides:
- **Objective assessment**: Removes emotional response to criticism
- **Evidence-based reasoning**: Backs up assessments with code analysis
- **Trade-off analysis**: Helps understand implications of changes
- **Confidence boost**: When feedback is wrong, validator confirms it

### Output Cleanliness
- Use bold headers with separator lines (visible in Claude Code)
- DO NOT use ### headings (render as faint gray)
- Group feedback by reviewer (letter system: A1, A2, B1, B2)
- Keep format consistent across all items
- Make priorities visually distinct with emojis

### Examples of Simple vs Complex Feedback

**Simple (don't validate)**:
- "Typo on line 45: 'teh' should be 'the'"
- "Missing semicolon on line 67"
- "This variable is declared but never used"
- "Can you explain why you chose approach X?"

**Complex (do validate)**:
- "This could cause performance issues at scale"
- "Consider using pattern X instead of Y for better maintainability"
- "This might be vulnerable to XSS"
- "The error handling here seems insufficient"
