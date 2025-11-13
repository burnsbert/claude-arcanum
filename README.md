# Claude Arcanum

I've been writing some articles and a lot of training docs lately for Claude Code, but I've decided to apply my talents to an open source library. This will serve as both a practical resource and as a model implementation for what's possible in Claude Code. You'll also notice that this is implemented as a plugin for easy installation, which is an underappreciated recently added feature to Claude Code.

This library contains a powerful core of functionality to supercharge your Claude Code experience. I've figured out some very effective ways to create very powerful workflows by integrating custom commands with agents, sometimes multiple agents, hyperspecialized for different tasks.

This is a collection of powerful custom commands and agents for Claude Code that enhance common developer tasks like troubleshooting tough problems, giving and receiving code reviews over github, deep research of difficult technical questions, and root cause analysis.

**📦 [Installation Instructions](INSTALL.md)** | **📚 Documentation Below**

## Overview

Claude Arcanum provides a comprehensive toolkit for Claude Code to supercharge development tasks.

### Features

**Agent-Powered Custom Commands**
- **arc-pr-review** - Three-pass validated code reviews on GitHub PRs. Give yourself a code review or run it on a PR you are code reviewing for a code review sidekick.
- **arc-pr-respond** - Helps you respond to a code review you have received on GitHub. Makes next steps easy with recommendations and being queued up to give Claude Code instructions for making requested adjustments to your code quickly.
- **arc-investigate** - This is the bunker buster missile for intractable problems. It burns a ton of tokens but can help get Claude Code unstuck.
- **arc-llm** - Generate prompts for external LLM consultation on the current issue. "Phone a friend"
- **arc-rca** - Root cause analysis with git forensics of the bug you just fixed or are fixing. Git blame is for amateurs.

**Agents** (Specialized intelligence engines)
- **arc-root-cause-analyzer** - Root cause analysis for bugs.
- **arc-deep-research** - Deep research that prioritizes completeness and correctness over speed and token efficiency. This is not for asking what the capital of Delaware is. This is for tricky questions that simpler research agents might bounce off of.
- **arc-technical-writer** - Elite technical documentation specialist for creating, checking, and modifying technical docs. Excels at researching codebases and writing clear, accurate documentation with proper verification passes.

### Architecture

Note: everything a user is meant to call has the arc- preface. Commands and agents with ca- are utility resources that the arc- commands and agents call, but aren't designed for direct use by the user.

```
Agent-Powered Commands        Agents (Internal)
──────────────────────────    ─────────────────────
/arc-pr-review ────────────▶  gh CLI + ca-code-review-validator (parallel)
/arc-pr-respond ───────────▶  gh CLI + ca-code-review-validator (parallel)

/arc-investigate ──────────▶  ca-store-problem-context (utility)
                 │            ca-brainstormer
                 └──────────▶ ca-problem-theory-validator (×5-6 parallel)

/arc-rca ──────────────────▶  arc-root-cause-analyzer

/arc-llm ──────────────────▶  ca-store-problem-context (utility)
                              + direct file reading

User-Invokable Agents         Use Cases
─────────────────────────     ───────────────────
arc-root-cause-analyzer  ──▶  Forensic bug analysis
arc-deep-research ───────────▶ Deep research (four-step methodology)
arc-technical-writer ────────▶ Technical documentation creation
```

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

**Reviewing a pull request?**
```
/arc-pr-review https://github.com/owner/repo/pull/123
```
Need a code review sidekick? Run this to get a comprehensive three-pass validated code review, and Claude Code all up to speed to be able to answer questions.

**Responding to PR feedback?**
```
/arc-pr-respond https://github.com/owner/repo/pull/123
```
Get validated analysis and prioritized response plan. Claude Code's context will be up to speed and ready to fix those nitpicks (and larger issues).

**Need technical documentation?**
```
Use the arc-technical-writer agent to create API documentation with examples.
```
Elite technical writer that researches your codebase and creates verified documentation.

## Structure

```
claude-arcanum/
├── commands/          # Custom slash commands for Claude Code
│   ├── arc-investigate.md
│   ├── arc-rca.md
│   ├── arc-llm.md
│   ├── arc-pr-review.md
│   ├── arc-pr-respond.md
│   └── ca-store-problem-context.md
├── agents/           # Custom agent definitions
│   ├── arc-root-cause-analyzer.md
│   ├── arc-deep-research.md
│   ├── arc-technical-writer.md
│   ├── ca-brainstormer.md
│   ├── ca-problem-theory-validator.md
│   └── ca-code-review-validator.md
├── scripts/          # Installation and utility scripts
└── README.md
```

---

### Custom Commands (GitHub Integration)

Direct commands that interact with GitHub via the `gh` CLI.

#### `/arc-pr-review` - Three-Pass Validated PR Review

**Purpose**: Perform comprehensive code review on GitHub pull requests with three-pass validation to ensure high-quality, accurate feedback.

**Prerequisites**: Requires GitHub CLI (`gh`). Command will automatically detect and offer to install on macOS/Linux/Windows if missing.

**Usage**:
```bash
/arc-pr-review https://github.com/owner/repo/pull/123
# or
/arc-pr-review 123
```
**Powered by** (in execution order):
1. GitHub CLI (`gh`) - Fetches PR data
2. Initial review - Comprehensive code review with checklist
3. `ca-code-review-validator` - Validates feedback items

---

#### `/arc-pr-respond` - Validated Feedback Analysis

**Purpose**: Analyze PR review feedback with validation, provide assessments, and create prioritized response plan.

**Prerequisites**: Requires GitHub CLI (`gh`). Command will automatically detect and offer to install on macOS/Linux/Windows if missing.

**Usage**:
```bash
/arc-pr-respond https://github.com/owner/repo/pull/123
/arc-pr-respond 123 humans              # Only human reviewers (not an ai reviewer like Code Rabbit)
/arc-pr-respond 123 fred and wilma      # Specific reviewers
```

**Powered by** (in execution order):
1. GitHub CLI (`gh`) - Fetches PR feedback
2. Initial categorization - Parses and categorizes all feedback
3. `ca-code-review-validator` - Validates complex items

---

#### `/arc-investigate` - Automated Troubleshooting

**Purpose**: Complete troubleshooting workflow that systematically investigates your problem and gives you evidence-based solutions.

**Powered by** (in execution order):
1. `ca-store-problem-context` (command) - Documents the problem
2. `ca-brainstormer` (agent) - Generates theories
3. `ca-problem-theory-validator` (agent × 5-6 in parallel) - Validates each theory

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
```
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

```
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

---

#### `arc-deep-research` - Four-Step Research Agent

**Purpose**: Deep investigative research using a four-step methodology that prioritizes correctness over speed. Ideal for complex technical questions that require thorough investigation, verification, and synthesis.

**This is a standalone research agent** - Unlike arc-root-cause-analyzer which is primarily called by `/arc-rca`, this agent is designed for direct invocation when you need comprehensive research.

**Four-Step Methodology**:

**Step 1 - Define the Research**:
- Clarifies key terms and their meaning in the codebase
- Determines scope (in/out/boundaries)
- Creates strategic research plan
- Breaks main question into specific subquestions

**Step 2 - Execute the Plan (First Pass)**:
- Systematically works through research plan
- Gathers evidence and answers subquestions
- Uses file:line references for all findings
- Identifies follow-up questions and gaps

**Step 3 - Follow-up Research (Second Pass)**:
- Chases leads from Step 2
- Fact-checks findings against actual code
- Verifies assumptions and fills gaps
- Resolves conflicts between documentation and implementation

**Step 4 - Revision and Final Draft**:
- Synthesizes all findings into polished response
- Organizes information logically with clear narrative
- Includes comprehensive file:line references
- Documents limitations and uncertainties
- Provides recommendations when applicable

**Usage** (via Task tool):
```
Use the arc-deep-research agent to investigate:

Question: How does the authentication workflow work from login to token validation?

Context: Working on bug related to session timeout, need to understand
complete auth flow including middleware, validation, and token refresh.
```

---

#### `arc-technical-writer` - Elite Technical Documentation Agent

**Purpose**: Create, check, and modify comprehensive technical documentation including markdown documents, code comments, and architectural documentation for developers and LLMs. Excels at researching codebases to understand implementation details, writing clear and accurate documentation, and performing thorough verification passes before finalizing.

**This is a standalone documentation agent** - Designed for direct invocation when you need high-quality technical documentation that requires codebase research and verification.

**Core Capabilities**:
- **Feature documentation** with architecture diagrams, examples, and troubleshooting
- **API documentation** with request/response formats, error codes, and usage patterns
- **Code comments** that explain complex logic, integration points, and gotchas
- **Bug pattern guides** (bugfinder.md) documenting common issues and prevention
- **Architecture documentation** with system overviews, data flows, and design decisions
- **Developer onboarding guides** and technical specifications

**Three-Phase Workflow**:

**Phase 1 - Research (30-40%)**:
- Locates and reads all relevant code files
- Traces data flows and component interactions
- Analyzes tests to understand expected behavior
- Reviews existing documentation for gaps or conflicts
- Takes detailed notes with file:line references

**Phase 2 - Drafting (30-40%)**:
- Organizes information into logical sections
- Writes clear prose with appropriate technical depth
- Adds code examples from the actual codebase
- Includes specific code references (file:line) throughout
- Links to related documentation

**Phase 3 - Verification (20-30%)**:
- Verifies every code reference is correct
- Tests all code examples
- Cross-checks claims against implementation
- Validates external links
- Ensures completeness and clarity

**Quality Standards**:
- Every technical claim backed by code reference (file:line)
- All examples tested and verified to work
- Written for target audience (developers, LLMs, or both)
- Comprehensive coverage of use cases and edge cases
- Structured for easy maintenance and updates

**Usage** (via Task tool):
```
Use the arc-technical-writer agent to document:

Task: Create comprehensive API documentation for the user authentication endpoints

Include: Request/response formats, error codes, authentication flow,
rate limits, and practical usage examples. Target audience: frontend
developers integrating with the API.
```

```
Use the arc-technical-writer agent to:

Task: Add detailed comments to the payment processing module explaining
how the different components interact, including edge cases and error handling.
```

```
Use the arc-technical-writer agent to create:

Task: A bugfinder.md documenting common bug patterns in our authentication
system, including detection strategies and prevention best practices.
```

## Notes

This project assumes that `.*.md` files (dot-prefixed markdown files) are gitignored in your projects. Working files and temporary documentation generated by these commands will use this naming pattern to avoid cluttering your repository.

Add this to your `.gitignore`:
```
/.*.md
```

## License

MIT License - See LICENSE file for details.
