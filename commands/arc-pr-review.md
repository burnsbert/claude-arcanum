---
description: Comprehensive code review of a GitHub PR with three-pass validation (review → vet feedback → final results)
allowed-tools: "*"
---

# Arc PR Review - Three-Pass Validated Code Review

Review GitHub PR: {{args}}

This command performs a three-pass review process:
1. **Pass 1**: Generate comprehensive code review feedback
2. **Pass 2**: Vet complex/uncertain/borderline feedback items using ca-code-review-validator
3. **Pass 3**: Generate final vetted results

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

## PASS 1: Initial Code Review

### Step 1.1: Fetch PR Information

Use the gh CLI to fetch:
- PR details: `gh pr view <number> --json title,body,author,labels,reviews,comments,files`
- Full diff: `gh pr diff <number>`
- Inline comments: `gh api repos/{owner}/{repo}/pulls/{number}/comments`

Also check locally if the repository exists for additional context about:
- Codebase structure and patterns
- Related files that might be affected
- Testing patterns and requirements
- Project-specific conventions in CLAUDE.md or similar files

**⚠️ IMPORTANT - CLAUDE.md Verification**: If you find CLAUDE.md or similar context or documentation files, do NOT assume claims about the codebase are accurate without verification. Always vet statements about code patterns, conventions, or architecture by examining the actual code. Context or documentation files may contain outdated, aspirational, or incorrect information.

### Step 1.2: Comprehensive Code Review Checklist

Perform a thorough review covering ALL of these areas:

#### 🗄️ Database & Data Layer
- [ ] **Schema/Data Migration**: Are migrations needed? Are they correct?
- [ ] **Migration Safety**: Can migrations run safely in production?
- [ ] **Rollback Plan**: Can migrations be rolled back if needed?
- [ ] **Data Integrity**: Will existing data remain valid?

#### 🧪 Testing
- [ ] **Unit Test Coverage**: Check if new/changed functions, methods, and classes have corresponding unit tests. Identify specific untested items by name and file:line.
- [ ] **API Test Coverage**: Check if new/changed API endpoints have corresponding API/integration tests. Identify specific untested endpoints by route and file:line.
- [ ] **Other Automated Tests**: Check if changes require updates to E2E, functional, or other automated tests in the repo. Identify specific gaps.
- [ ] **Changed Interfaces**: If function/method signatures changed, verify tests were updated to match new parameters/return types. Identify specific outdated tests.
- [ ] **Test Quality**: Do tests actually verify the functionality (not just hit lines)?
- [ ] **Edge Cases**: Are boundary conditions and error cases tested?
- [ ] **Test Patterns**: Do tests follow project conventions?

**IMPORTANT**: For any missing or inadequate test coverage, you MUST identify the file names and lines for the code that needs more test coverage and provide a clear description of what test coverage is needed.

#### ⚡ Performance
- [ ] **Performance Impact**: Will changes affect response times?
- [ ] **Database Queries**: Are queries optimized? Any N+1 problems?
- [ ] **Caching**: Should results be cached? Is cache invalidation handled?
- [ ] **Resource Usage**: Memory/CPU implications of changes?

#### 📚 Documentation
- [ ] **Docblocks**: Are functions/methods properly documented?
- [ ] **API Documentation**: Are API changes documented?
- [ ] **Comments**: Is complex logic explained?
- [ ] **README Updates**: Do setup/config changes need documentation?

#### 🐛 Common Bugs
- [ ] **"Dave's not here"**: Checking undefined object properties (e.g., `$foo->bar->baz` when `$foo->bar` might be null)
- [ ] **Null/Undefined Checks**: Proper validation before using variables?
- [ ] **Type Safety**: Are types checked/cast appropriately?
- [ ] **Array Access**: Safe array access with isset() or null coalescing?

#### 🔐 Security & Permissions
- [ ] **Permissions**: Are authorization checks in place?
- [ ] **Access Control**: Can users only access what they should?
- [ ] **Input Validation**: Is user input validated and sanitized?
- [ ] **SQL Injection**: Are queries parameterized?
- [ ] **XSS Prevention**: Is output properly escaped?

#### 🎨 Frontend & Styling
- [ ] **CSS Changes**: Are styles scoped appropriately?
- [ ] **Responsive Design**: Do changes work on mobile/tablet?
- [ ] **Cross-browser**: Tested in required browsers?
- [ ] **Accessibility**: ARIA labels, keyboard navigation?
- [ ] **Asset Loading**: Are images/fonts optimized?

#### 🏗️ Code Quality
- [ ] **Code Patterns**: Does code follow project conventions?
- [ ] **DRY Principle**: Is there unnecessary duplication?
- [ ] **Error Handling**: Are errors caught and handled properly?
- [ ] **Logging**: Are important operations logged?
- [ ] **Clean Code**: Is the code readable and maintainable?

#### 🔄 Integration & Dependencies
- [ ] **Breaking Changes**: Will this break existing functionality?
- [ ] **API Contracts**: Are API interfaces maintained?
- [ ] **Dependencies**: Are new dependencies necessary and secure?
- [ ] **Feature Flags**: Should this be behind a feature flag?

### Step 1.3: Generate Initial Feedback

**CRITICAL REQUIREMENT**: Every piece of feedback MUST include:
- **File name(s)**: The exact file path(s) being referenced
- **Line number(s)**: The specific line(s) where the issue/concern/suggestion applies

Structure initial feedback as a list with categories:

```markdown
## Pass 1: Initial Review Feedback

### 🚨 Critical Issues (Must Fix)
1. **[Issue Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Problem**: [What's wrong]
   - **Suggested Solution**: [How to fix]
   - **Confidence**: [High/Medium/Low]

### ⚠️ Important Concerns (Should Fix)
1. **[Concern Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Issue**: [What could be better]
   - **Suggestion**: [Recommended approach]
   - **Confidence**: [High/Medium/Low]

### 💭 Minor Suggestions (Consider)
1. **[Suggestion Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Current**: [Current approach]
   - **Alternative**: [Suggested improvement]
   - **Confidence**: [High/Medium/Low]
```

**For each feedback item, include a "Confidence" rating**:
- **High**: Clearly correct, obvious issue, well-established best practice
- **Medium**: Likely correct but involves trade-offs or judgment calls
- **Low**: Subjective, style preference, or uncertain about context

---

## PASS 2: Vet Feedback Items

### Step 2.1: Identify Items Needing Validation

Review all feedback from Pass 1 and identify items that need vetting. Items should be vetted if they meet ANY of these criteria:

**MUST VET**:
- Confidence level is Medium or Low
- Involves subjective judgment or trade-offs
- Style/convention feedback (could be nitpick)
- Performance suggestions (need to verify impact)
- Architectural recommendations (need wisdom check)
- Items in "Important Concerns" or "Minor Suggestions" categories

**DO NOT VET** (skip these to save time):
- Confidence level is High AND in "Critical Issues"
- Obvious security vulnerabilities
- Clear bugs (null pointer, undefined variable, etc.)
- Missing required tests (factual, not subjective)
- Obvious breaking changes

### Step 2.2: Run Batch Validation

Compile all feedback items identified in Step 2.1 into a single list and invoke the ca-code-review-validator agent **once**:

**Use the Task tool with the complete list**:

```
Review the following list of code review feedback items and validate them:

**Item 1**
File: [file:line]
Category: [Critical/Important/Minor]
Confidence: [High/Medium/Low]
Feedback: "[Complete feedback text]"

**Item 2**
File: [file:line]
Category: [Critical/Important/Minor]
Confidence: [High/Medium/Low]
Feedback: "[Complete feedback text]"

[... all items needing validation ...]

Context: PR [brief description of PR goal]
```

### Step 2.3: Process Batch Validation Results

The ca-code-review-validator will return batch results organized as:
- **Items to KEEP**: Feedback that should remain (✅ FULLY ENDORSE / ⚠️ ENDORSE WITH CAVEATS)
- **Items to REMOVE**: False positives, nitpicks, or invalid feedback (❌ DISAGREE / 🔵 MINOR/NITPICK / 🎯 OUT OF SCOPE)
- **Items Needing Clarification**: Feedback requiring more context (🤔 DEPENDS/CLARIFY)

Extract the verdicts before proceeding to Pass 3.

---

## PASS 3: Generate Final Vetted Results

### Step 3.1: Synthesize Feedback

For each feedback item:

**If NOT vetted** (was obvious/high confidence):
- Include as-is in final review

**If vetted and verdict is ✅ FULLY ENDORSE**:
- Include in final review
- May add brief note: "(Validated)"

**If vetted and verdict is ⚠️ ENDORSE WITH CAVEATS**:
- Include in final review
- Add validator's caveats/trade-offs to the feedback
- Adjust confidence if needed

**If vetted and verdict is ❌ DISAGREE**:
- REMOVE from final review
- Optionally note in internal summary what was removed and why

**If vetted and verdict is 🔵 MINOR/NITPICK**:
- Move to "Minor Suggestions" if not already there
- Add note: "(Low priority - style/preference)"
- Consider removing if there are many other items

**If vetted and verdict is 🤔 DEPENDS/CLARIFY**:
- Rewrite feedback to ask for clarification
- Example: "Clarification needed: [original concern]. Context needed: [what validator said]"

**If vetted and verdict is 🎯 OUT OF SCOPE**:
- REMOVE from PR feedback
- Optionally suggest creating separate issue/PR

### Step 3.2: Final Review Output Format

```markdown
# PR Review: [PR Title]

## 📋 Summary
[Brief description of what the PR does and overall assessment]

## ✅ Positive Aspects
- [What's done well] - `filename.ext:line`
- [Good patterns followed] - `filename.ext:line`

## 🚨 Critical Issues (Must Fix Before Merge)
[Only include high-confidence issues or validated concerns]

1. **[Issue Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Problem**: [What's wrong]
   - **Solution**: [How to fix]
   [If validated: **Validated**: [Brief validator insight]]

## ⚠️ Important Concerns (Strongly Recommend Fixing)
[Include validated concerns with caveats noted]

1. **[Concern Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Issue**: [What could be better]
   - **Suggestion**: [Recommended approach]
   [If validated with caveats: **Trade-offs**: [Note from validator]]

## 💭 Minor Suggestions (Consider If Time Allows)
[Include minor items, marked nitpicks appropriately]

1. **[Suggestion Type]**: [Description]
   - **File**: `path/to/file.ext:line`
   - **Current**: [Current approach]
   - **Alternative**: [Suggested improvement]
   [If nitpick: **Note**: Style preference, not blocking]

## 📊 Checklist Summary
- Database/Migration: [✅/⚠️/❌]
- Test Coverage: [✅/⚠️/❌]
- Performance: [✅/⚠️/❌]
- Documentation: [✅/⚠️/❌]
- Security: [✅/⚠️/❌]
- Code Quality: [✅/⚠️/❌]

## 🎯 Overall Assessment

**Recommendation**: [Approve / Request Changes / Needs Discussion]

[Summary paragraph incorporating validation insights]

## 📝 Validation Summary (Internal)
[Optional section showing what was validated]

- **Items Reviewed**: [Total feedback items from Pass 1]
- **Items Validated**: [How many ran through ca-code-review-validator]
- **Endorsements**: [Items fully endorsed]
- **Items Removed**: [Feedback removed after validation with brief why]
- **Adjustments Made**: [How validation changed the review]
```

### Step 3.3: Present Results

Present the final vetted review to the user. The validation process should be mostly invisible - the final review should just be higher quality and more confident feedback.

Optionally include a brief note at the end:
```
---
*This review used three-pass validation: initial review, feedback vetting via ca-code-review-validator, and synthesis of validated results.*
```

---

## Priority Guidelines

Focus on these in order of importance:
1. **Security vulnerabilities** - Always highest priority
2. **Data corruption risks** - Schema/migration issues
3. **Breaking changes** - API/functionality breaks
4. **Performance regressions** - Significant slowdowns
5. **Missing tests** - Critical path coverage
6. **Code maintainability** - Long-term impact
7. **Style/formatting** - Lowest priority (likely to be filtered as nitpicks)

---

## Important Notes

### Efficiency Considerations
- **Batch validation**: Single ca-code-review-validator call for all items needing validation
- **Selective vetting**: Only vet items that need it (skip obvious issues)
- **Time budget**: Validator performs quick sanity checks on most items, deep investigation only when needed

### Quality Standards
- **Every feedback item must have file:line references**
- **Confidence ratings must be honest** (enables proper vetting)
- **Validator verdicts must be respected** (don't override without good reason)
- **Final review should be cleaner** (removed nitpicks, strengthened valid concerns)

### When Validation Disagrees
If ca-code-review-validator disagrees with your initial feedback:
- **Trust the validator** - It does deep investigation
- **Don't argue** - Remove or adjust the feedback
- **Learn from it** - Understand why the validator disagreed

### Output Cleanliness
The final review should feel like a single pass, not three passes. Don't clutter with:
- "This was validated and..."
- Long explanations of validation process
- Internal validator reasoning (unless it adds value)

Keep validation notes minimal and embedded naturally in the feedback.
