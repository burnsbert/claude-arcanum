---
name: vet-apply
description: Apply recommendations from a prior /vet or /vet-wf run. Investigates each Recommended Change before touching anything, implements only what is clearly warranted, and reports back on what was changed, what was skipped, and anything that needs discussion. Run immediately after /vet or /vet-wf.
allowed-tools: Read, Edit, Write, MultiEdit, Glob, Grep, Bash
argument-hint: "[items]"
user-invocable: true
---

# Vet Apply

Apply the recommendations produced by a previous `/vet` or `/vet-wf` run. Investigate each item before acting. Implement only changes that are unambiguously correct. Skip everything else and explain why.

## Usage

```
/vet-apply [items]
```

Run immediately after `/vet` or `/vet-wf`. The recommendations from that run must be visible in the current conversation.

`[items]` is optional. If omitted, all recommendations are processed. If provided, only matching recommendations are processed. Supported formats:
- Numbers: `1,3,5` or `1-3` or `1,3-5`
- Natural language: `"the null checks"`, `"security items"`, `"anything about error handling"`

## Process

### Step 0: Parse Arguments

If `$ARGUMENTS` is non-empty, extract a filter from it:
- If `$ARGUMENTS` consists entirely of digits, commas, hyphens, and whitespace, treat it as **numeric**: parse comma-separated numbers and ranges (e.g. `1,3-5`) into a set of item numbers
- Otherwise treat it as **natural language**: a semantic description to match against recommendation titles/descriptions

Store this as `FILTER` (or null if no arguments).

### Step 1: Extract Recommendations

Read the most recent `/vet` or `/vet-wf` output in this conversation. Extract every item from the **Recommended Changes** section. Ignore Optional Improvements and Dismissed sections — don't act on those.

If no vet/vet-wf output is visible in the conversation, stop and say: "No vet output found in this conversation. Run `/vet` or `/vet-wf` first, then `/vet-apply`."

If `FILTER` is set, narrow the extracted list to only matching items:
- **Numeric filter**: keep only items whose number is in the parsed set
- **Natural language filter**: keep items whose title or description semantically matches the filter — use judgment, err toward exclusion on ambiguous matches; if a match is borderline, flag it under Needs Discussion rather than applying it
- If the filter matches nothing, say: "No recommendations matched `{$ARGUMENTS}`. Available items: {numbered list of titles}." then stop.

### Step 2: Investigate Each Recommendation

For every recommendation, **read the actual code before deciding**. Do not implement anything based on the recommendation text alone.

For each item:

1. **Locate the referenced file and line** — use Read, Grep, or Glob to find the exact code
2. **Verify the claim** — does the problem actually exist as described?
3. **Check if already fixed** — did a prior change in this conversation already address it?
4. **Assess correctness** — is the proposed fix clearly right, or does it have tradeoffs?

**Apply the change if ALL of these are true:**
- The problem demonstrably exists in the code (you can quote the line)
- The fix is unambiguous (one clear correct solution, not a judgment call)
- Applying it won't break other things (no side effects to reason through)
- It's not a style preference or subjective improvement

**Skip the change if ANY of these are true:**
- You can't confirm the problem exists after reading the code
- The fix is already in place
- The correct solution requires tradeoffs or depends on intent
- It's a naming/style preference
- It would require broader refactoring beyond the specific issue

### Step 3: Apply Approved Changes

For each approved change, make the edit directly using Edit, Write, or MultiEdit.

Keep a mental log as you go:
- `APPLIED`: implemented, what was changed
- `SKIPPED`: not implemented, specific reason
- `NEEDS DISCUSSION`: real issue but fix isn't obvious — flag for user

### Step 4: Report Results

After processing all recommendations, output:

```
## Vet Apply Results

### Applied ({N} changes)
{Numbered list — what was changed and why it was clearly warranted}
  - File: `path/to/file:line`
  - Change: [one-line description]

### Skipped ({N} items)
{Numbered list — what was skipped and the specific reason}
  - Rec #{N}: [brief title]
  - Reason: [couldn't confirm / already fixed / tradeoff / style]

### Needs Discussion ({N} items, or "None")
{Items that are real issues but don't have an obvious fix}
  - [Description of issue and why the fix isn't clear-cut]
```

If nothing was applied: "Nothing applied. All recommendations were skipped or already addressed." Then explain each skip.

## Important

- **Investigate first, always** — never apply based on recommendation text alone
- **Conservative by default** — when in doubt, skip and flag
- **One change at a time** — complete and verify each edit before moving to the next
- **Don't expand scope** — fix exactly what was identified, nothing more
- **No style changes** — if the only problem is aesthetics or naming convention, skip it
