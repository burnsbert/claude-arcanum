# PR Respond File Format

The orchestrator writes respond results to `.code-reviews/` in this exact format. The file is both human-readable markdown and machine-parseable by `respond-to-html.py`.

## Filename Convention

`.code-reviews/<pr-number>-respond-<YYYY-MM-DD-HHMM>.md`

Examples:
- `.code-reviews/7654-respond-2026-04-07-1430.md`

## Format

```markdown
---
title: "PR title"
risk: 6
recommendation: request-changes
pr_url: https://github.com/owner/repo/pull/123
head_ref: feature/my-branch
type: respond
---

## Intent
[2-3 sentence problem-first synthesis]

## Changes
[High-level summary of what changed]

## Risk
[One sentence explaining the key risk drivers]

## Results
[What the respond analysis found - overall quality signal]

## Critical Feedback

### A1. Sort comparator inverted
**File**: `src/services/UserWorkload.php:160-178`
**Comment**: https://github.com/owner/repo/pull/123#discussion_r12345
**Comment IDs**: 12345
**Reviewers**: Jamie R., CodeRabbit
**Severity**: critical
**Bugfinder**: Confirmed (BF-1)

> **Jamie R.**: The comparator in `getSuggestedUsersForWindow` uses `$b - $a` which sorts descending (busiest first), but the docblock says "ranked from least to most busy."
>
> **CodeRabbit**: `getSuggestedUsersForWindow` sorts by `$b - $a` (descending), contradicting the stated intent of ranking least-to-most busy. Also, `$windowStart` is passed as both date arguments.

**Additional notes**: Two confirmed bugs in the same method - the inverted sort and the ignored `$windowEnd` parameter.

**Suggested change**: Change comparator to `$a - $b` and use `$windowEnd->format('Y-m-d')` as the second date argument.

**Recommended action**: Valid, should fix. Both bugs confirmed by multiple reviewers.

### B2. Missing null check on user schedule
**File**: `src/services/UserSchedule.php:40-42`
**Reviewers**: Morgan T.
**Severity**: critical

> **Morgan T.**: `getUsersAvailability` doesn't check if `$user->getSchedule()` returns null before calling methods on it. Users without schedules will throw a fatal error.

**Suggested change**: Add a null check and skip users with no schedule, or return a default availability object.

**Recommended action**: Valid, should fix before merge. Fatal error on a common edge case.

## Important Feedback

### A3. Canceled appointments counted as unavailable
**File**: `src/services/UserSchedule.php:119-125`
**Reviewers**: Jamie R., Morgan T.
**Severity**: important

> **Jamie R.**: The status filter includes STATUS_CANCELED_BY_ADMIN and STATUS_CANCELED_BY_USER. Canceled items shouldn't count against availability.
>
> **Morgan T.**: Why are canceled statuses included here? `getUserWorkloadScores` in the same class doesn't include them.

**Additional notes**: Inconsistent with the established pattern in the same class.

**Suggested change**: Remove the two canceled statuses from the filter.

**Trade-offs**: Validator noted that some teams may want canceled-but-not-yet-rescheduled items to block the slot temporarily.

**Recommended action**: Valid. Inconsistent with the pattern in the same class. Worth fixing now.

## Minor Feedback

### B1. Variable naming could be clearer
**File**: `src/services/UserWorkload.php:48`
**Reviewers**: Morgan T.
**Severity**: minor

> **Morgan T.**: `$wl` is not very descriptive. Consider `$workloadScore` or `$userWorkload` for readability.

**Suggested change**: Rename `$wl` to `$workloadScore`.

**Recommended action**: Valid, minor cleanup. Quick fix.

## Nitpick Feedback

### A4. Consider using early return
**File**: `src/services/UserWorkload.php:95`
**Reviewers**: CodeRabbit
**Severity**: nitpick

> **CodeRabbit**: The nested if/else in `evaluateAssignmentReadiness` could be flattened with early returns for better readability.

**Recommended action**: Judgment call. Either style works - the current nesting matches adjacent methods in this class.

## Invalid Feedback

### A5. Missing database index
**File**: `src/services/UserWorkload.php:84`
**Reviewers**: CodeRabbit
**Severity**: invalid

> **CodeRabbit**: The absence query would benefit from an index on (user_id, absence_date) for performance.

**Recommended action**: Incorrect - there's already a composite index on (user_id, date) at line 35 of the migration that covers this query pattern.

## Question Feedback

### Q1. Why is BUSINESS_DAY_STARTS_AT set to 8 rather than configurable?
**File**: `src/services/UserSchedule.php:12`
**Comment**: https://github.com/owner/repo/pull/123#discussion_r3046384400
**Comment IDs**: 3046384400
**Reviewer**: Jamie R.

> **Jamie R.**: Why is this hardcoded to 8? Is this intentional?

**Proposed answer**: Yes, intentional. The constant matches the existing `BUSINESS_HOURS_START` in `CompanySettings.php:45` which is used across scheduling logic. Making it configurable per-company would require threading the setting through `UserSchedule`, `WorkloadCalculator`, and `AssignmentBoard` - a larger scope change tracked in PROJ-4521.

## Positive Comments

### P1. Nice test coverage on edge cases
**Comment**: https://github.com/owner/repo/pull/123#discussion_r3046384401
**Comment IDs**: 3046384401
**Reviewer**: Morgan T.

> **Morgan T.**: Really thorough test coverage here, especially on the edge cases.

## Handled Feedback
3 issues from reviewers were already resolved or addressed.

### H1. [CodeRabbit] Sort inversion in comparator
**File**: `UserWorkload.php:176`
**Reviewer**: CodeRabbit
**Status**: Resolved - thread marked resolved

### H2. [Jamie R.] Missing null check
**File**: `Job.php:42`
**Reviewer**: Jamie R.
**Status**: Resolved - author replied "Fixed in latest commit"

## Checklist
- Database: N/A
- Test Coverage: WARN
- Performance: PASS
- Documentation: WARN
- Security: N/A
- Code Quality: WARN
- Scope: PASS

## Assessment
[Concluding paragraph about overall state and recommended next steps]

## Validation
- Pass 1 items: 11
- Bugfinder items: 0
- Kept: 8
- Clarify: 2
- Removed: 1
```

## Parsing Rules

- **Frontmatter**: YAML between `---` markers. `risk` is integer 1-10. `recommendation` is one of: `approve`, `request-changes`, `needs-discussion`. `head_ref` is the PR head branch name (used to construct GitHub file links). `pr_url` is the full PR URL. `type` is always `respond`.
- **Sections**: `## Heading` marks a section. Section names are exact: Intent, Changes, Risk, Results, Critical Feedback, Important Feedback, Minor Feedback, Nitpick Feedback, Invalid Feedback, Question Feedback, Positive Comments, Handled Feedback, Checklist, Assessment, Validation.
- **Findings**: `### ID. Title` starts a finding. ID format: single uppercase letter + number (`A1`, `B2`, `C1`), or `BF-1` for bugfinder-only findings, or `H1` for handled findings, or `Q1` for questions, or `P1` for positive comments. `Q` and `P` are reserved prefixes — the orchestrator must never assign these letters to reviewers.
- **File line**: `**File**: \`path:line\`` or `**File**: \`path:startline-endline\`` immediately after the finding heading. Use the range format when the reviewer comment spans multiple lines (e.g., `UserWorkload.php:95-96`).
- **Comment URL**: `**Comment**: <url>` is a direct link to the first reviewer's comment on GitHub. Always present for reviewer findings. For BF-* findings, omit this field. The HTML converter uses this as the link target for the file reference instead of constructing a link to the raw file.
- **Comment IDs**: `**Comment IDs**: 12345,67890` is a comma-separated list of GitHub comment IDs for this finding. Always present for reviewer findings. Use the `comment_ids` array from the pass1 JSON output. For deduped multi-reviewer items, include all reviewers' comment IDs. The HTML converter uses these to do exact sidecar matching, injecting the correct original comment(s) into the finding's expandable section. Without this field, matching falls back to imprecise line-range overlap which can show the wrong original comment for adjacent findings.
- **Reviewers line**: `**Reviewers**: Name1, Name2` lists all reviewers who raised this issue. Uses display names (first name + last initial when available, else username).
- **Severity line**: `**Severity**: critical|important|minor|nitpick|invalid` classifies the feedback.
- **Bugfinder line**: `**Bugfinder**: Confirmed (BF-N)` — optional, present only when the local bugfinder independently flagged the same issue as this reviewer finding. The ID matches the BF-N item that was deduplicated into this finding. Appears after `**Severity**:` and before the reviewer blockquote.
- **Reviewer comments**: Verbatim reviewer text in a blockquote section. Each reviewer's comment is on its own line prefixed with `> **Reviewer Name**:`. When multiple reviewers raised the same issue (deduplication), show each reviewer's comment separately, separated by `>` blank lines within the blockquote. For single-reviewer findings, still use the `> **Name**:` format. Always present for reviewer findings. For BF-* findings (bugfinder-only), omit this section.
- **Additional notes**: `**Additional notes**:` is optional. Use only when there is meaningful context to add beyond what the reviewers said - e.g., related bugs in the same method, inconsistencies with other code, or context no reviewer mentioned. Do NOT use this to rephrase what any reviewer already said.
- **Action labels**: `**Suggested change**:` is the standard label for suggested fixes. `**Trade-offs**:` may follow if the validator returned caveats. Omit `**Suggested change**:` if the reviewer's comment already contains a clear suggestion and there's nothing to add.
- **Recommended action**: `**Recommended action**:` followed by senior developer guidance on the same line. Not a draft reply - this is Claude's assessment of the feedback. Examples: "Valid, should fix.", "Judgment call, either approach works.", "Incorrect - the index already exists.", "Valid but low priority, consider for follow-up."
- **Field order within a finding**: Title, File, Comment (URL), Comment IDs, Reviewers, Severity, Bugfinder (optional), Reviewer comments (blockquote), Additional notes (optional), Suggested change (optional), Trade-offs (optional), Recommended action.
- **ID assignment**: Reviewers are assigned letters in order of first appearance (A for first reviewer encountered, B for second, etc.). Issues are numbered within each reviewer's letter: A1, A2, A3, B1, B2. If multiple reviewers raise the same issue, it keeps the letter of whoever mentioned it first but lists all reviewers in the `**Reviewers**:` line.
- **Sorting**: Within the file, findings are grouped by severity section (Critical first, Invalid last). Within each section, findings appear in ID order.
- **Bugfinder findings**: BF-* IDs for findings raised only by the bugfinder (not overlapping with any reviewer feedback). Placed in the appropriate severity section based on their category. BF-* findings do NOT have a reviewer comments blockquote since they originate from the bugfinder, not a reviewer. Instead, they use a plain body paragraph describing the bug.
- **Question Feedback**: Entries use `Q1`, `Q2`, etc. IDs. Field order: `**File**:` (when pass1 resolved a file location), `**Comment**:`, `**Comment IDs**:`, `**Reviewer**:` (singular), then the blockquote, then optionally `**Proposed answer**:` (present when pass1 could answer the question from the code; omitted when the question can't be answered from code alone). No `**Recommended action**:` field. Omit the section if there are no questions.
- **Positive Comments**: Entries use `P1`, `P2`, etc. IDs. Field order: `**File**:` (when pass1 resolved a file location), `**Comment**:`, `**Comment IDs**:`, `**Reviewer**:` (singular), then the blockquote. No `**Recommended action**:` field. Omit the section if there are no positive comments.
- **Handled Feedback**: First line after heading is a summary sentence with the count. Entries use `H1`, `H2`, etc. IDs. Each has `**File**:`, `**Reviewer**:` (singular), and `**Status**:` lines. No body paragraph needed.
- **Empty sections**: If a severity has no findings, omit the section entirely. Question Feedback, Positive Comments, and Handled Feedback are all optional - omit if empty.
- **Checklist**: `- Label: STATUS` where STATUS is PASS, WARN, FAIL, or N/A.
- **Validation**: `- Label: N` key-value pairs.
- **Disclaimer**: Always include as the last line of the file, after all sections: `Warning: This report was generated by AI, and AI can make mistakes. Make sure to verify these findings before acting on them.`
