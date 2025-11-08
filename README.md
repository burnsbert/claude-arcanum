# Claude Arcanum

A collection of powerful custom commands and agents for Claude Code that enhance problem-solving, debugging, and root cause analysis workflows.

## Overview

Claude Arcanum provides a comprehensive toolkit for debugging, code review, and problem-solving in Claude Code.

### V1 Features

**Custom Commands** (Direct GitHub integration)
- **arc-pr-review** - Perform code reviews on GitHub pull requests 🚧 *Planned*
- **arc-pr-respond** - Assist in responding to code review comments 🚧 *Planned*

**Agent-Powered Commands** (Intelligent problem-solving)
- **arc-investigate** - Automated troubleshooting with theory validation ✅ *Built*
- **arc-llm** - Generate prompts for external LLM consultation ✅ *Built*
- **arc-rca** - Root cause analysis with git forensics ✅ *Built*

**Agents** (Specialized intelligence engines)
- **arc-root-cause-analyzer** - Forensic bug analysis ✅ *Built*
- **arc-researcher** - Two-pass investigative research (prioritizes correctness) 🚧 *Planned*

### Architecture

```
Custom Commands                GitHub API
────────────────────          ──────────────────
/arc-pr-review ────────────▶  Pull request analysis + gh CLI
/arc-pr-respond ───────────▶  Comment generation + gh CLI

Agent-Powered Commands        Agents (Internal)
──────────────────────────    ─────────────────────
/arc-investigate ──────────▶  ca-brainstormer
                 │            ca-problem-theory-validator (×5-6 parallel)
                 │
                 └─────────▶  ca-store-problem-context (utility)

/arc-rca ──────────────────▶  arc-root-cause-analyzer

/arc-llm ──────────────────▶  ca-store-problem-context (utility)
                              + direct file reading

User-Invokable Agents         Use Cases
─────────────────────────     ───────────────────
arc-root-cause-analyzer  ──▶  Forensic bug analysis
arc-researcher ─────────────▶ Deep research (two-pass methodology)
```

### What This Toolkit Provides

- **Faster debugging** - Evidence-based problem analysis and theory validation
- **Better code reviews** - Systematic PR review with comprehensive checklists
- **Root cause understanding** - Git forensics to trace bugs to their origin
- **Prevention insights** - Learn from mistakes to prevent future issues
- **External help** - Generate prompts for consulting other LLMs
- **Deep research** - Two-pass investigative methodology for complex questions

## Quick Start

**Stuck on a bug?**
```
/arc-investigate
```
Gets theories, validates them, and gives you ranked next steps.

**Just fixed a bug?**
```
/arc-rca
```
Understand how it was introduced and how to prevent similar issues.

**Need external help?**
```
/arc-llm
```
Generate a comprehensive prompt for ChatGPT, Gemini, or other LLMs.

**Reviewing a pull request?** 🚧 *Coming Soon*
```
/arc-pr-review https://github.com/owner/repo/pull/123
```
Get a comprehensive code review with detailed analysis.

**Responding to PR feedback?** 🚧 *Coming Soon*
```
/arc-pr-respond https://github.com/owner/repo/pull/123
```
Craft thoughtful responses to code review comments.

## Structure

```
claude-arcanum/
├── commands/          # Custom slash commands for Claude Code
│   ├── arc-investigate.md
│   ├── arc-rca.md
│   ├── arc-llm.md
│   └── ca-store-problem-context.md
├── agents/           # Custom agent definitions
│   ├── arc-root-cause-analyzer.md
│   ├── ca-brainstormer.md
│   └── ca-problem-theory-validator.md
├── scripts/          # Installation and utility scripts
└── README.md
```

## Commands

Commands are organized into two categories: direct GitHub integration commands and agent-powered problem-solving commands.

---

### Custom Commands (GitHub Integration)

Direct commands that interact with GitHub via the `gh` CLI.

#### `/arc-pr-review` - Pull Request Code Review 🚧 *Planned*

**Purpose**: Perform comprehensive code review on GitHub pull requests with systematic analysis.

**Usage**:
```bash
/arc-pr-review https://github.com/owner/repo/pull/123
```

**What it will do**:
- Fetch PR details using `gh` CLI
- Analyze changed files and diffs
- Review code for common issues, bugs, and improvements
- Check for test coverage
- Verify documentation updates
- Generate structured review with categorized feedback

**When to use**:
- Before approving a pull request
- When conducting thorough code reviews
- To ensure consistent review quality across the team

**Status**: Planned for v1 - not yet implemented

---

#### `/arc-pr-respond` - PR Review Response Assistant 🚧 *Planned*

**Purpose**: Assist in crafting thoughtful, professional responses to code review comments on your pull requests.

**Usage**:
```bash
/arc-pr-respond https://github.com/owner/repo/pull/123
```

**What it will do**:
- Fetch PR and review comments using `gh` CLI
- Analyze feedback and understand context
- Help draft responses to reviewer comments
- Suggest code changes to address feedback
- Generate commit messages for review-driven changes

**When to use**:
- Responding to code review feedback
- Addressing reviewer concerns systematically
- Ensuring professional communication in reviews

**Status**: Planned for v1 - not yet implemented

---

### Agent-Powered Commands (Problem-Solving)

Intelligent commands that use specialized agents for deep analysis. These are your main entry points for debugging and problem-solving.

---

#### `/arc-investigate` - Automated Troubleshooting

**Purpose**: Complete troubleshooting workflow that systematically investigates your problem and gives you evidence-based solutions.

**Powered by**:
- `ca-store-problem-context` (command) - Documents the problem
- `ca-brainstormer` (agent) - Generates theories
- `ca-problem-theory-validator` (agent × 5-6 in parallel) - Validates each theory

**How It Works**:
1. **Documents the problem** - Captures what you've been working on from the current session
2. **Generates theories** - Creates 5-6 hypotheses about what's causing the issue
3. **Validates in parallel** - Tests each theory through code investigation (runs simultaneously for speed)
4. **Ranks results** - Organizes findings into actionable categories
5. **Presents action plan** - Gives you clear next steps

**Results Categories**:
- 🔴 **PROVEN** - Confirmed root causes (fix these immediately!)
- 🟡 **High Confidence** - Strong evidence but needs verification
- 🟢 **Worth Investigating** - Plausible but needs more data
- ⚫ **Ruled Out** - Disproven theories (don't waste time here)

**Usage**:
```bash
# Let Claude extract problem from current session
/arc-investigate

# Use an existing problem context file
/arc-investigate .problem.20250108-143022.md
```

**Example Session**:
```
You: I'm stuck on this rendering bug in UserProfile
[... debugging conversation ...]

You: /arc-investigate

Claude: Investigating the rendering issue in UserProfile...

Generated 5 theories. Validating in parallel...

# Investigation Results

## 🔴 PROVEN Root Causes

### State Mutation at Line 45
**Evidence**: Direct mutation of state array found
**Fix**: Use immutable update pattern
**Steps**:
1. Change tasks.push() to setTasks([...tasks, newTask])
2. Verify re-rendering works
3. Check for similar patterns elsewhere

## 🟡 High Confidence

### Missing Key Props in List
**Evidence**: React warning in console, no keys on mapped elements
**Verification needed**: Add keys and check if residual issues remain

## ⚫ Ruled Out

### Stale Closure in useEffect
**Why**: Effect dependencies are correct, cleanup properly implemented

---

What would you like to do?
1. Fix the proven state mutation issue
2. Verify the key props theory
3. Generate external LLM prompt
```

**When to Use**:
- ✅ You're stuck on a problem and don't know where to start
- ✅ You want to explore multiple possible causes efficiently
- ✅ You need evidence-based direction, not guesses
- ✅ You want to avoid going down wrong debugging paths

**Pro Tips**:
- Run this early when stuck - don't spend hours debugging manually first
- The parallel validation makes this fast (5-6 theories validated simultaneously)
- If all theories are uncertain, consider using `/arc-llm` for external perspective
- You can re-run with additional context if initial results aren't conclusive

---

#### `/arc-rca` - Root Cause Analysis

**Purpose**: Forensic investigation that traces bugs back to their origin, helping you understand how they were introduced and how to prevent them in the future.

**Powered by**:
- `arc-root-cause-analyzer` (agent) - Performs forensic git analysis

**How It Works**:
1. **Extracts context** - Automatically gathers info from your session (or uses provided details)
2. **Determines status** - Figures out if bug is fixed or still being worked on
3. **Git forensics** - Uses git blame, git log, and history analysis
4. **Analyzes intent** - Understands what the original developer was trying to do
5. **Classifies cause** - Identifies the type of mistake (logic error, edge case, refactor issue, etc.)
6. **Vets fix** - For fixed bugs, checks if the solution is complete and sound
7. **Finds similar risks** - Searches for other code with the same pattern
8. **Prevention recommendations** - Suggests how to prevent this category of bug

**Usage**:
```bash
# Auto-extract from current session (most common)
/arc-rca

# Analyze a specific commit
/arc-rca commit abc123

# Analyze a specific bug by description
/arc-rca "authentication tokens expiring immediately"

# Analyze a bug with ticket reference
/arc-rca JIRA-1234
```

**Example Session** (After Fixing a Bug):
```
You: [Just fixed token expiration bug and committed]

You: /arc-rca

Claude: Analyzing root cause of token expiration bug...

# Root Cause Analysis Report

## Bug Summary
Authentication tokens expired immediately instead of 24 hours

**Status**: Fixed in commit abc123
**Affected**: src/auth/tokenService.ts

## Root Cause Investigation

**Breaking Change**:
- Commit: def456abc
- Date: 2024-12-15 14:32:18 -0500
- Author: Joe Developer <joe@example.com>
- Message: "Refactor: Extract time constants to utilities"

**Original Intent**: Refactor to eliminate magic numbers

**What Happened**:
- Developer created time.DAY constant (86400000 ms)
- Used it with jwt.sign({ expiresIn: time.DAY })
- JWT library expects SECONDS, not milliseconds
- Tokens expired in 86.4 seconds instead of 86,400 seconds

**Classification**: Integration Issue
- JWT library API expects seconds
- JavaScript time constants use milliseconds
- Mismatch wasn't caught in testing

## Fix Quality Assessment

**Status**: ✅ Fixes the immediate issue
**Concerns**:
- Similar bug found in redis.ts:34 (same pattern)
- Fix uses magic number (multiply by 1000)
- Better approach: Create time.toSeconds() utility

## Similar Bug Risk

Found 1 other location with same pattern:
- `src/cache/redis.ts:34` - Uses time.HOUR for Redis TTL
  **Action Required**: Likely has same bug, needs immediate fix

## Prevention Recommendations

**Testing**: Add integration test for token expiration duration
**Code Review**: Check unit expectations when refactoring time constants
**Tooling**: TypeScript branded types for Milliseconds vs Seconds
**Documentation**: Document units in time utility comments
**Process**: Create conversion utilities (toSeconds, toMillis)

---

What would you like to do?
1. Fix the similar bug in redis.ts
2. Create time.toSeconds() utility
3. Add integration tests
4. See full detailed analysis
```

**Example Session** (Unfixed Bug):
```
You: [Working on memory leak, haven't fixed it yet]

You: /arc-rca

Claude: Analyzing root cause of memory leak...

The bug appears to be unfixed. Based on investigation:

**Likely Introduced**: commit xyz789 (WebSocket refactor)
**Suspected Issue**: Event listeners not being cleaned up
**Affected**: src/services/socketService.ts:67

**Recommendation**: The analysis is preliminary since the bug isn't
fixed yet. For a complete root cause analysis, fix the bug first
and re-run /arc-rca to get full timeline, fix vetting, and prevention
recommendations.

Would you like to:
1. See investigation details
2. Use /arc-investigate for systematic debugging
3. Continue with manual debugging
```

**When to Use**:
- ✅ **After fixing a bug** - Understand how it was introduced (best time!)
- ✅ **During post-mortems** - Learn from production incidents
- ✅ **Before merging fixes** - Verify your fix is complete
- ✅ **When patterns repeat** - Understand why the same bugs keep happening
- ✅ **For code reviews** - Analyze bugs found during review

**Pro Tips**:
- Run this immediately after fixing a bug while context is fresh
- The git forensics can trace bugs back months or years
- Similar bug detection often finds other instances of the same mistake
- Prevention recommendations help improve your team's processes
- For unfixed bugs, you'll get preliminary insights but full analysis requires a fix

---

#### `/arc-llm` - External LLM Consultation

**Purpose**: Generates a comprehensive, self-contained prompt that you can copy-paste into ChatGPT, Google Gemini, or any other LLM to get external help.

**Powered by**:
- `ca-store-problem-context` (command) - Documents the problem
- Direct file reading and code extraction (no agents)

**Why This Exists**: Sometimes you need a second opinion or want to consult a specialized model. This command packages up your entire problem with all necessary code context so the other LLM doesn't need filesystem access.

**How It Works**:
1. **Documents problem** - Captures your current issue from the session
2. **Reads all relevant files** - Extracts code sections mentioned in the problem
3. **Includes architecture** - Adds framework, dependencies, project structure
4. **Packages context** - Creates 200-500 lines of comprehensive, standalone prompt
5. **Displays for copying** - Shows the prompt ready to paste elsewhere

**Usage**:
```bash
# Extract from current session
/arc-llm

# Use existing problem context
/arc-llm .problem.20250108-143022.md
```

**Example Output**:
```
Generated LLM consultation prompt (copy the text below):

────────────────────────────────────────────────

# Problem Consultation Request

I need help solving a rendering issue in my React + TypeScript project.

## Problem Description

UserProfile component doesn't re-render when user data changes. The state
update happens (confirmed via console logs) but the UI remains stale.

## Project Context

**Framework/Stack**: React 18.2 + TypeScript 5.0 + Vite
**Key Dependencies**:
- react: 18.2.0
- react-router-dom: 6.8.0

**Project Structure**:
```
src/
├── components/
│   ├── UserProfile.tsx  (problem here)
│   └── ...
├── hooks/
│   └── useUserData.ts   (state management)
└── types/
    └── user.ts          (type definitions)
```

## Relevant Code

### src/components/UserProfile.tsx
```typescript
// Lines 1-65
import React, { useState, useEffect } from 'react';
import { useUserData } from '../hooks/useUserData';
import { User } from '../types/user';

export const UserProfile: React.FC = () => {
  const { user, updateUser } = useUserData();

  const handleUpdate = (newData: Partial<User>) => {
    // State update happens here
    updateUser(newData);
    console.log('Updated:', newData); // This logs correctly
  };

  return (
    <div>
      <h1>{user.name}</h1>  {/* This doesn't update! */}
      <p>{user.email}</p>
      <button onClick={() => handleUpdate({ name: 'New Name' })}>
        Update Name
      </button>
    </div>
  );
};
```

**Context**: Main profile component. The console.log shows updates happening
but the rendered name stays the same.

### src/hooks/useUserData.ts
```typescript
// Lines 1-30
import { useState } from 'react';
import { User } from '../types/user';

export const useUserData = () => {
  const [user, setUser] = useState<User>({
    name: 'John Doe',
    email: 'john@example.com'
  });

  const updateUser = (updates: Partial<User>) => {
    // Line 45: Direct mutation (suspicious!)
    Object.assign(user, updates);
    setUser(user);
  };

  return { user, updateUser };
};
```

**Context**: Custom hook for user state management.

### src/types/user.ts
```typescript
// Lines 1-10
export interface User {
  name: string;
  email: string;
  avatar?: string;
}
```

## What's Been Tried

1. Added console.logs - confirmed state updates are called
2. Checked React DevTools - state shows old value
3. Tried forcing re-render with key prop - didn't help
4. Verified component is properly imported and used

## Error Messages / Symptoms

No error messages in console. Component simply doesn't reflect state changes.
Console logs show the update function is called with correct data.

## Questions

1. Why isn't the component re-rendering when state changes?
2. Is there an issue with how we're updating state in the custom hook?
3. What's the proper pattern for this use case?

────────────────────────────────────────────────

Ready to copy! Paste this into:
- ChatGPT (chat.openai.com)
- Google Gemini (gemini.google.com)
- Claude (claude.ai)
- Any other LLM
```

**What Makes This Different from .problem.md**:
- **.problem.md** uses file:line references (assumes filesystem access)
- **arc-llm output** includes all code inline (no filesystem needed)
- **.problem.md** is for internal use or sharing with Claude
- **arc-llm output** is for external LLMs without context

**When to Use**:
- ✅ `/arc-investigate` didn't find the solution
- ✅ You want a second opinion from a different AI model
- ✅ You need specialized expertise (e.g., specific framework knowledge)
- ✅ You want to consult a model with different training data
- ✅ You're working on a problem that benefits from multiple perspectives
- ✅ You need to share the problem with a colleague who uses a different LLM

**Pro Tips**:
- The generated prompt is already well-formatted for LLMs
- Code snippets include line numbers as comments for reference
- Architectural context helps other LLMs understand your setup
- You can edit the prompt before pasting if you want to add more context
- Works great with specialized models (e.g., Gemini for Google Cloud issues)

---

### Utility Commands (ca-*)

#### ca-store-problem-context

Creates a `.problem.[timestamp].md` file documenting the current problem you're working on. This file is formatted as a detailed prompt to an LLM, including relevant context, file references, and questions. Useful for:
- Getting help from another LLM or AI system
- Documenting complex problems for later reference
- Creating reproducible problem reports

**Usage**: `/ca-store-problem-context`

## Agents

### User Agents (arc-*)

These agents can be invoked directly using the Task tool for specialized analysis.

---

#### `arc-root-cause-analyzer` - Forensic Bug Analysis Agent

**Purpose**: Deep forensic investigation that uses git history to trace bugs back to their origin, understand why they happened, and provide actionable prevention strategies.

**This is the engine behind `/arc-rca`** - You typically use `/arc-rca` command instead of calling this agent directly, but you can invoke it directly for custom analysis workflows.

**How It Works**:
1. **Git archaeology** - Uses git blame, git log, and git history to find when buggy code was introduced
2. **Context analysis** - Reads commit messages, PR descriptions, and related changes to understand developer intent
3. **Timeline construction** - Maps out when bug was introduced, discovered, and fixed
4. **Root cause classification** - Categorizes the mistake (logic error, edge case, incomplete refactor, integration issue, etc.)
5. **Fix vetting** - For fixed bugs, analyzes if the solution is complete, correct, and sustainable
6. **Pattern detection** - Searches codebase for similar code that might have the same bug
7. **Prevention synthesis** - Recommends specific testing, tooling, documentation, and process improvements

**Usage** (via Task tool):
```
Use the arc-root-cause-analyzer agent to analyze:

Bug: Authentication tokens expiring immediately
Status: Fixed in commit abc123
Files: src/auth/tokenService.ts
What changed: Modified expiresIn calculation from time.DAY to time.DAY / 1000
```

**What You Get**:

**1. Breaking Change Analysis**
- Exact commit that introduced the bug
- What the code looked like before and after
- What the developer was trying to accomplish
- Related changes that provide context

**2. Root Cause Classification**
Choose from categories like:
- Logic Error (incorrect implementation)
- Edge Case (missing handling of uncommon scenario)
- Incomplete Refactoring (refactor missed updating related code)
- Integration Issue (components interact unexpectedly)
- Dependency Change (library behavior changed)
- Merge Conflict (conflict resolution introduced bug)
- Specification Gap (requirements unclear)

**3. Timeline Analysis**
- When bug was introduced
- How long before discovery
- Time to fix
- Key events in the bug's lifecycle

**4. Fix Quality Assessment** (for fixed bugs)
- Is the fix complete or a workaround?
- Does it address root cause or just symptoms?
- Could it introduce new issues?
- Are there tests to prevent regression?
- Confidence level in the fix

**5. Similar Bug Detection**
- Other locations with the same pattern
- Risk assessment for each location
- Recommended audit tasks

**6. Prevention Recommendations**
Specific suggestions across:
- **Testing**: What tests would have caught this?
- **Code Review**: What should reviewers look for?
- **Tooling**: What linters/types/tools would help?
- **Documentation**: What docs would prevent this?
- **Process**: What process changes would help?

**Example Direct Invocation**:
```
You: I need forensic analysis on the caching bug we had last week

Claude: [Uses Task tool to invoke arc-root-cause-analyzer]

Agent produces:

# Root Cause Analysis Report

## Breaking Change
**Commit**: def789abc
**Date**: 2024-11-15 16:45:22 -0500
**Author**: Bob Smith <bob@example.com>
**Message**: "Optimize cache key generation"
**Intent**: Improve performance by simplifying cache keys

**What Changed**:
```javascript
// Before (working)
const cacheKey = `${userId}_${resource}_${timestamp}`;

// After (introduced bug)
const cacheKey = `${userId}_${resource}`; // Removed timestamp!
```

**Root Cause**: Logic Error + Performance Optimization Gone Wrong
- Developer removed timestamp to increase cache hits
- Didn't realize timestamp was preventing stale data bugs
- Cache now serves stale data across requests

## Fix Quality Assessment
**Status**: ⚠️ Workaround, not root cause fix
**Current fix**: Added cache TTL of 5 seconds
**Problem**: Doesn't address why timestamp was removed
**Better approach**: Keep timestamp, use Redis cache with intelligent invalidation

## Similar Bugs Found
- `src/services/profileCache.ts:45` - Same pattern, same risk
- `src/utils/apiCache.ts:23` - Similar but has TTL already

## Prevention
**Testing**: Integration test with concurrent requests would have caught this
**Code Review**: Performance changes should verify correctness isn't broken
**Process**: Performance optimizations need explicit approval from tech lead
```

**When to Use Directly**:
- Building custom workflows that need RCA as part of a larger process
- Analyzing multiple bugs in batch
- Integrating with external tools or scripts
- Creating automated post-mortem reports

**Note**: Most users should use `/arc-rca` command instead, which calls this agent automatically.

---

#### `arc-researcher` - Two-Pass Research Agent 🚧 *Planned*

**Purpose**: Deep investigative research using a two-pass methodology that prioritizes correctness over speed. Ideal for complex technical questions that require thorough investigation.

**This is a standalone research agent** - Unlike arc-root-cause-analyzer which is primarily called by `/arc-rca`, this agent is designed for direct invocation when you need comprehensive research.

**Two-Pass Methodology**:

**Pass 1 - Broad Discovery**:
- Casts a wide net across the codebase, documentation, and related resources
- Identifies all potentially relevant information
- Maps out the landscape of the problem space
- Generates initial hypotheses and areas to investigate

**Pass 2 - Rigorous Verification**:
- Deeply investigates the most promising leads from Pass 1
- Verifies claims against actual code and documentation
- Tests hypotheses through systematic examination
- Eliminates false positives and incorrect assumptions
- Synthesizes findings into accurate, comprehensive answer

**Usage** (via Task tool):
```
Use the arc-researcher agent to investigate:

Question: How does the authentication flow work from login to token validation?

Context: Working on bug related to session timeout, need to understand
complete auth flow including middleware, validation, and token refresh.
```

**What You Get**:

**1. Discovery Summary**
- All relevant files, functions, and components identified
- Related documentation and comments found
- Initial hypotheses about the answer

**2. Verification Results**
- Each hypothesis tested and verified/rejected
- Code evidence for confirmed findings
- Corrections to initial assumptions

**3. Comprehensive Answer**
- Accurate, detailed explanation backed by code
- File and line references for every claim
- Flow diagrams or step-by-step breakdowns where helpful
- Related considerations and edge cases

**4. Confidence Assessment**
- What is definitively confirmed
- What remains uncertain or ambiguous
- Recommendations for further investigation if needed

**Example Direct Invocation**:
```
You: I need to understand how the caching layer works with Redis

Claude: [Uses Task tool to invoke arc-researcher]

Agent produces:

# Research Report: Redis Caching Layer

## Discovery Phase
Found 3 primary files implementing caching:
- src/cache/redisClient.ts - Connection and client management
- src/cache/cacheService.ts - High-level caching API
- src/middleware/cacheMiddleware.ts - Express middleware

Initial hypothesis: Two-tier caching (memory + Redis)

## Verification Phase
Confirmed: Two-tier architecture with L1 (in-memory) and L2 (Redis)
- L1 cache: src/cache/memoryCache.ts:15-89
- TTL: 60 seconds for L1, 3600 seconds for L2
- Invalidation: Pub/sub pattern using Redis channels

Rejected: Initial assumption about cache-aside pattern
- Actually uses write-through for critical data
- Cache-aside only for read-heavy endpoints

## Complete Flow
[Detailed explanation with file:line references...]

## Confidence Assessment
✅ Confirmed: Architecture, TTL values, invalidation strategy
⚠️ Uncertain: Behavior during Redis outage (no explicit fallback code found)
📋 Recommend: Review disaster recovery documentation
```

**When to Use Directly**:
- Complex technical questions requiring thorough research
- Understanding unfamiliar codebases or architectural patterns
- Investigating intricate data flows across multiple systems
- When you need high-confidence, verified answers (not quick guesses)
- Debugging issues that require deep system understanding
- Planning major refactors or architectural changes

**Prioritizes Correctness Over Speed**:
- Takes longer than simple searches (2-pass methodology)
- Worth the time when accuracy is critical
- Reduces the risk of pursuing wrong approaches based on incorrect assumptions

**Status**: Planned for v1 - not yet implemented

---

### Utility Agents (ca-*)

#### ca-brainstormer

Analyzes a problem and generates 5-6 evidence-based theories about what might be causing it. The agent investigates the codebase first, checking basic assumptions and gathering evidence before suggesting causes.

**Usage**:
- Provide a problem context file (`.problem.[timestamp].md`) when invoking
- Or provide a detailed problem description in the same format
- If no problem file exists, create one first (either with `/ca-store-problem-context` or manually in the same style)

**What it does**:
- Verifies basic assumptions (files exist, imports correct, syntax valid, etc.)
- Investigates relevant files and recent changes
- Generates 5-6 possible causes ordered by likelihood
- Provides evidence, causal explanation, and verification steps for each theory

**Example**: "Use the ca-brainstormer agent with the problem context from `.problem.20250108-143022.md`"

#### ca-problem-theory-validator

Rigorously vets a single theory about a problem's cause through systematic investigation. Attempts to prove or disprove the theory, and if neither is conclusive, provides concrete steps to gather the necessary data.

**Usage**:
- Provide a problem context file (`.problem.[timestamp].md`)
- Specify which theory to validate (by number or full text)
- If no problem file exists, create one first (via `/ca-store-problem-context` or manually)

**What it does**:
- Investigates each claim in the theory systematically
- Gathers supporting and contradicting evidence with file references
- Verifies assumptions through code examination and testing
- Reaches one of three conclusions: PROVEN, DISPROVEN, or UNCERTAIN
- Provides actionable next steps based on the conclusion

**Example**: "Use the ca-problem-theory-validator agent to validate theory #2 from `.problem.20250108-143022.md`"

## Typical Workflows

### Workflow 1: Stuck on a Bug

```
1. Try debugging manually (5-10 min)
2. Still stuck? → /arc-investigate
3. Get ranked theories with evidence
4. If PROVEN cause found → fix it
5. If uncertain → /arc-llm for second opinion
6. After fix → /arc-rca for prevention insights
```

### Workflow 2: Just Fixed a Critical Bug

```
1. Commit your fix
2. → /arc-rca (auto-extracts from session)
3. Review root cause analysis
4. Check "Similar Bug Risk" section
5. Fix similar bugs if found
6. Implement prevention recommendations
7. Document lessons learned
```

### Workflow 3: Post-Mortem Analysis

```
1. Gather info (bug description, fix commit)
2. → /arc-rca commit abc123
3. Get comprehensive forensic report
4. Share prevention recommendations with team
5. Create follow-up tasks for:
   - Similar bug audits
   - New tests
   - Process improvements
```

### Workflow 4: Systematic Debugging Session

```
1. Encounter problem
2. → /arc-investigate (get theories)
3. Pick highest confidence theory
4. Try to verify/fix
5. If still stuck → /arc-llm
6. Paste into ChatGPT/Gemini
7. Get external perspective
8. After fix → /arc-rca
9. Learn and prevent
```

## Quick Reference

### Custom Commands (GitHub Integration)

| Command | When to Use | Status |
|---------|-------------|--------|
| `/arc-pr-review [url]` | Review pull requests systematically | 🚧 Planned |
| `/arc-pr-respond [url]` | Respond to PR review feedback | 🚧 Planned |

### Agent-Powered Commands (Problem-Solving)

| Command | When to Use | Powered By | Output | Status |
|---------|-------------|------------|--------|--------|
| `/arc-investigate` | Stuck on bug, need systematic analysis | `ca-brainstormer`, `ca-problem-theory-validator` (agents) | Ranked theories with evidence | ✅ Built |
| `/arc-rca` | Just fixed bug, want to understand origin | `arc-root-cause-analyzer` (agent) | Root cause report with prevention tips | ✅ Built |
| `/arc-llm` | Need second opinion from external LLM | `ca-store-problem-context` (command) + file reading | Copy-pasteable prompt with all context | ✅ Built |

### User Agents

| Agent | Role | Used By | Invoke Via | Status |
|-------|------|---------|-----------|--------|
| `arc-root-cause-analyzer` | Forensic git analysis | `/arc-rca` | Task tool or `/arc-rca` command | ✅ Built |
| `arc-researcher` | Two-pass research (prioritizes correctness) | Direct invocation | Task tool only | 🚧 Planned |

### Utility Agents (Internal)

| Agent | Role | Used By | Status |
|-------|------|---------|--------|
| `ca-brainstormer` | Generate theories | `/arc-investigate` | ✅ Built |
| `ca-problem-theory-validator` | Validate single theory | `/arc-investigate` (×5-6 parallel) | ✅ Built |
| `ca-store-problem-context` | Extract problem context | `/arc-investigate`, `/arc-llm` | ✅ Built |

## Installation

Installation scripts coming soon.

## FAQ & Tips

### How do these tools work together?

**arc-investigate** → Finding the bug (generates & validates theories)
**arc-rca** → Understanding the bug (traces origin, prevents recurrence)
**arc-llm** → Getting external help (packages problem for other LLMs)

They complement each other: investigate to find, rca to understand, llm for second opinions.

### Which commands use which agents?

Commands are orchestrators that use agents under the hood:

- **`/arc-investigate`** uses:
  - `ca-brainstormer` agent (generates theories)
  - `ca-problem-theory-validator` agent (validates each theory in parallel)

- **`/arc-rca`** uses:
  - `arc-root-cause-analyzer` agent (forensic git analysis)

- **`/arc-llm`** uses:
  - No agents - directly reads files and generates prompts

You rarely need to invoke agents directly - the commands handle it for you.

### When should I use /arc-investigate vs /arc-rca?

- **Before fixing**: Use `/arc-investigate` - helps you find and fix the bug
- **After fixing**: Use `/arc-rca` - helps you understand and prevent it

### Can I use arc-rca on unfixed bugs?

Yes! It will provide preliminary insights but recommends re-running after the fix for complete analysis including fix vetting and timeline.

### Do I need to provide information to these commands?

Usually no - they extract context from your current Claude Code session. You can provide specific details if needed (like commit hashes or bug IDs).

### What if arc-investigate doesn't find the answer?

- Review the "Worth Investigating" theories and gather suggested data
- Use `/arc-llm` to get a second opinion from ChatGPT or Gemini
- Re-run with more specific problem description
- Sometimes bugs need deeper manual investigation first

### How long does /arc-investigate take?

Typically 1-2 minutes. The parallel validation of theories makes it fast - all 5-6 theories are checked simultaneously.

### Does arc-rca work on old bugs?

Yes! As long as the code is in git history, it can trace back months or years to find when the bug was introduced.

### Can I use these tools for non-bugs?

- **arc-investigate**: Yes, works for any technical problem (performance issues, unexpected behavior, configuration problems)
- **arc-rca**: Primarily for bugs, but can analyze any problematic code change
- **arc-llm**: Works for any problem you need help with

### What's the .problem.*.md file for?

Internal working file that captures problem context with file:line references. Used by other commands as input. Follows the `.*.md` gitignore pattern.

### Do I need to install anything?

Installation scripts coming soon. For now, manually copy the command and agent files to your Claude Code configuration directories.

## Naming Conventions

- **arc-*** - Top-level commands and agents designed for direct use by users
- **ca-*** - Utility commands and agents used internally by the top-level arc- commands

## Notes

This project assumes that `.*.md` files (dot-prefixed markdown files) are gitignored in your projects. Working files and temporary documentation generated by these commands will use this naming pattern to avoid cluttering your repository.

Add this to your `.gitignore`:
```
/.*.md
```

## License

MIT License - See LICENSE file for details.
