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

**Team-Based Workflows** (Agent teams with dynamic parallel investigation)
- **arc-research-team** - Parallel deep research using a team of 3 researcher agents investigating independent threads simultaneously, with a dedicated synthesizer producing a cohesive final report. For complex, multi-faceted questions that benefit from breadth-first parallel investigation.
- **arc-war-room** - Team-based parallel investigation for intractable bugs. Brainstorms theories, dispatches investigators in parallel, dynamically spawns new investigators when promising leads are discovered mid-investigation. The heavy artillery when arc-investigate isn't enough.

**Creative Ideation** (Multi-round idea generation and ranking)
- **arc-think-tank** - Creative ideation workflow that generates, critiques, evolves, and ranks ideas toward a goal. 5 rounds of thinking (Opus+ultrathink), vetting (Sonnet), and riffing (Opus) — each round with randomly assigned personalities that change how agents reason, evaluate, and evolve ideas. Final judge (Opus, personality-neutral) produces a ranked report. 17 serial agent calls, comparable to arc-war-room in scope.

**Semi-Autonomous Development** (Story-to-PR pipeline)
- **arc-maestro** - 10-phase pipeline from story to implementation. Researches codebase, creates plan, implements tasks with specialist routing, validates each task. Handles Jira tickets or local story files.
- **arc-maestro-review** - Code review and PR creation. Two-pass review with enhanced bug-finding, fixes bugs with regression tests, creates PR.

**Skills** (Conversational tools)
- **rubber-duck** - A trusted peer developer for talking through technical ideas, designs, and plans. Follows a structured conversation flow: listen and understand, explore together, strengthen the idea, and summarize. Asks one question at a time, uses codebase research to verify claims, and gives honest feedback without being a rubber stamp or a blocker.

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

/arc-research-team ────────▶  ca-research-agent (×3 parallel, team)
                 └──────────▶ ca-research-synthesizer (team)

/arc-war-room ────────────▶  ca-store-problem-context (utility)
                 │            ca-brainstormer (ultrathink)
                 └──────────▶ ca-war-room-investigator (×3-5 dynamic, team)

/arc-think-tank ──────────▶  ca-think-tank-thinker (×5 serial, ultrathink)
                 │            ca-think-tank-vetter (×6 serial)
                 │            ca-think-tank-riffer (×5 serial)
                 └──────────▶ ca-think-tank-judge (final report)

/arc-maestro ────────────▶  ca-maestro-scout
                 │            ca-maestro-planner
                 │            ca-maestro-plan-reviewer
                 │            ca-maestro-junior-dev-doer (Haiku)
                 │            ca-maestro-dev-doer (Sonnet)
                 │            ca-maestro-senior-dev-doer
                 │            ca-maestro-frontend-dev-doer
                 │            ca-maestro-devops-dev-doer
                 │            ca-maestro-task-validator (Haiku)
                 │            ca-maestro-senior-task-validator (Sonnet)
                 └──────────▶ ca-maestro-ui-validator (Opus)

/arc-maestro-review ─────▶  ca-maestro-code-review
                 └──────────▶ ca-maestro-code-review-responder

User-Invokable Agents         Use Cases
─────────────────────────     ───────────────────
arc-root-cause-analyzer  ──▶  Forensic bug analysis
arc-deep-research ───────────▶ Deep research (four-step methodology)
arc-technical-writer ────────▶ Technical documentation creation
```

## Quick Start

**Need to implement a story?**
```
/arc-maestro JIRA-123
/arc-maestro ./stories/my-story.md
```
Researches, plans, implements, and validates. Review with `/arc-maestro-review`.

**Stuck on a bug?**
```
/arc-investigate
```
Gets theories, validates them, and gives you ranked next steps.

**Stuck on a *really* tough bug?**
```
/arc-war-room
```
Like arc-investigate but with a persistent team that chases new leads as they emerge during investigation.

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

**Complex research question with multiple facets?**
```
/arc-research-team How does auth work across the frontend, API, and database layers?
```
Decomposes your question into independent threads, dispatches 3 parallel researchers, and synthesizes a cohesive report.

**Need creative ideas for a goal or problem?**
```
/arc-think-tank How can we reduce customer churn for our SaaS product? ./data/churn-analysis.csv
```
5 rounds of ideation, critique, and evolution — produces a ranked top-5 report with scores, risks, and next steps.

## Structure

```
claude-arcanum/
├── commands/          # Custom slash commands for Claude Code
│   ├── arc-think-tank.md
│   ├── arc-investigate.md
│   ├── arc-rca.md
│   ├── arc-llm.md
│   ├── arc-pr-review.md
│   ├── arc-pr-respond.md
│   ├── arc-research-team.md
│   ├── arc-war-room.md
│   ├── arc-maestro.md
│   ├── arc-maestro-review.md
│   └── ca-store-problem-context.md
├── agents/           # Custom agent definitions
│   ├── arc-root-cause-analyzer.md
│   ├── arc-deep-research.md
│   ├── arc-technical-writer.md
│   ├── ca-brainstormer.md
│   ├── ca-code-review-validator.md
│   ├── ca-think-tank-thinker.md
│   ├── ca-think-tank-vetter.md
│   ├── ca-think-tank-riffer.md
│   ├── ca-think-tank-judge.md
│   ├── ca-problem-theory-validator.md
│   ├── ca-research-agent.md
│   ├── ca-research-synthesizer.md
│   ├── ca-war-room-investigator.md
│   ├── ca-maestro-scout.md
│   ├── ca-maestro-planner.md
│   ├── ca-maestro-plan-reviewer.md
│   ├── ca-maestro-junior-dev-doer.md
│   ├── ca-maestro-dev-doer.md
│   ├── ca-maestro-senior-dev-doer.md
│   ├── ca-maestro-frontend-dev-doer.md
│   ├── ca-maestro-devops-dev-doer.md
│   ├── ca-maestro-task-validator.md
│   ├── ca-maestro-senior-task-validator.md
│   ├── ca-maestro-ui-validator.md
│   ├── ca-maestro-code-review.md
│   ├── ca-maestro-code-review-responder.md
│   └── personalities/    # Personality definitions for think-tank
│       ├── contrarian.md
│       ├── pragmatist.md
│       ├── visionary.md
│       └── connector.md
├── skills/           # Conversational skills
│   └── rubber-duck/
│       └── SKILL.md
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

#### `/arc-research-team` - Team-Based Parallel Deep Research

**Purpose**: Orchestrate a team of parallel researcher agents to investigate complex, multi-faceted research questions. Decomposes the question into independent threads, dispatches 3 researchers to investigate simultaneously, then synthesizes findings into a cohesive report.

**Powered by**:
- `ca-research-agent` (agent × 3, team-based parallel) - Independent thread investigation
- `ca-research-synthesizer` (agent) - Combines findings into unified report
- Claude Code agent teams (TeamCreate, SendMessage, shared TaskList)

**How It Works**:
1. **Decomposes** your question into 3-6 independent research threads
2. **Creates a team** with shared task list and spawns 3 researcher agents
3. **Researchers self-organize** — claiming tasks, investigating, reporting findings, and picking up new tasks
4. **Follow-up tasks** discovered during research are added dynamically (capped at 12 total)
5. **Synthesizer** combines all findings into a cohesive report organized by theme
6. **Cleanup** — team is shut down, resources cleaned up, follow-up options presented

**When to Use This vs arc-deep-research**:
- Use `arc-deep-research` for single focused questions needing depth
- Use `arc-research-team` for multi-faceted questions with 3+ independent threads needing breadth

**Usage**:
```bash
/arc-research-team How does the plugin system work in this repository?
/arc-research-team What's the full impact of upgrading from React 17 to 18?
/arc-research-team How does auth work across the frontend, API, and database layers?
```

---

#### `/arc-war-room` - Team-Based Parallel Investigation

**Purpose**: War room for intractable bugs. Brainstorms theories, dispatches a persistent team of investigators to validate them in parallel, dynamically spawns new investigators when promising leads are discovered mid-investigation, and synthesizes ranked results with next steps.

**Powered by**:
- `ca-brainstormer` (agent, ultrathink) - Theory generation
- `ca-war-room-investigator` (agent × 3-5, team-based dynamic) - Theory validation
- Claude Code agent teams (TeamCreate, SendMessage, shared TaskList)

**How It Works**:
1. **Documents the problem** using existing problem context or creating one
2. **Brainstorms theories** via ca-brainstormer with ultrathink for deep analysis
3. **Assembles a war room** — creates team, tasks for each theory, spawns 3 investigators
4. **Investigators validate theories** in parallel, reporting findings and new discoveries
5. **Dynamic adaptation** — lead creates new tasks for discovered leads, spawns additional investigators (up to 5) when needed
6. **Lead synthesizes** all findings into ranked results with cross-theory pattern detection
7. **Cleanup** — team shut down, actionable next steps presented

**When to Use This vs arc-investigate**:
- Use `arc-investigate` for standard debugging — fixed theories, efficient parallel validation
- Use `arc-war-room` for tough problems where investigation may reveal new leads that need chasing

**Usage**:
```bash
# Auto-extract problem from current session
/arc-war-room

# With specific problem context
/arc-war-room .problem.20250208-143022.md
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

---

#### `/arc-think-tank` - Creative Ideation Workflow

**Purpose**: Generate, critique, evolve, and rank creative ideas toward a user-provided goal. Produces a ranked report of the top 5 ideas with scores, risks, and next steps.

**Powered by** (17 serial agent calls):
- `ca-think-tank-thinker` (agent × 5, Opus + ultrathink) - Generates 5 ideas per round
- `ca-think-tank-vetter` (agent × 6, Sonnet) - Evaluates ideas with (+N) consensus system
- `ca-think-tank-riffer` (agent × 5, Opus) - Evolves the most promising idea each round
- `ca-think-tank-judge` (agent × 1, Opus) - Ranks top 5 with scoring and clustering

**How It Works**:
1. **Parse goal and materials** from arguments, create session context files
2. **5 rounds of ideation**, each consisting of:
   - **Personality assignment** — orchestrator randomly assigns a personality to each agent (no consecutive repeats)
   - **Thinker** generates 5 new ideas (with ultrathink for deep creative analysis) using assigned personality
   - **Vetter** evaluates all ideas, adding comments or incrementing (+N) consensus markers, guided by assigned personality
   - **Riffer** picks the idea with the most improvement potential and creates an evolved version, guided by assigned personality
   - **Personality logging** — selections logged to task context for resume support
3. **Final vetting pass** gives all ideas one last evaluation (with assigned personality)
4. **Judge** (personality-neutral) clusters redundant ideas, selects strongest representatives, and ranks the top 5
5. **Report** with ranked ideas, scores, risks, next steps, honorable mentions, and themes

**Context Files Created**:
- `.task-{id}.md` - Session context (goal, materials, progress)
- `.think-tank-{id}-ideas.md` - All ideas with comments and consensus signals
- `.think-tank-{id}-report.md` - Final ranked report

**Usage**:
```bash
# Goal only
/arc-think-tank How can we improve developer onboarding?

# Goal with material files
/arc-think-tank How can we reduce customer churn? ./data/churn-analysis.csv ./docs/roadmap.md

# Resume interrupted session (auto-detects from .task-tt-*.md)
/arc-think-tank

# Add more rounds to an existing session
/arc-think-tank +2
```

**Personality System**:

Each round of the think-tank assigns a random personality to each agent (thinker, vetter, riffer). Personalities affect reasoning style, evaluation criteria, and what the agent prioritizes — not just tone, but substantive behavioral differences. The orchestrator ensures no agent uses the same personality in consecutive rounds.

**Four Personalities**:

- **Contrarian** — Challenges assumptions, inverts conventional wisdom. Criteria: Originality > Impact > Feasibility. Values intellectual courage and breaking orthodoxy. Suspicious of consensus thinking and incrementalism.

- **Pragmatist** — Focused on what's buildable now with real constraints. Criteria: Feasibility > Impact > Originality. Values incremental progress and clear implementation paths. Suspicious of ambitious moonshots and dependency chains.

- **Visionary** — No constraints, big swings. Criteria: Impact > Originality > Feasibility. Values transformative change and long-term vision. Suspicious of incrementalism and playing it safe.

- **Connector** — Cross-domain analogies and pattern matching. Criteria: Originality > Impact > Feasibility (via cross-pollination). Values importing proven patterns from other fields. Suspicious of siloed thinking and reinventing solutions.

**How Personalities Work**:
- Auto-assigned randomly at the start of each round via bash randomness (not LLM "random")
- No consecutive repeats — each agent gets a different personality than it had in the previous round
- Logged per round in the task context file for resume support
- Judge remains personality-neutral — synthesizes all ideas on their merits regardless of source personality

---

#### `/arc-maestro` - Semi-Autonomous Development Pipeline

**Purpose**: 10-phase pipeline that takes a story (from Jira or a local file) and drives it from research through implementation. Researches codebase, creates plan, implements tasks with specialist routing, validates each task, and prepares for code review.

**Powered by** (in execution order):
- `ca-maestro-scout` (agent) - Codebase researcher
- `ca-maestro-planner` (agent) - Task decomposer
- `ca-maestro-plan-reviewer` (agent) - Quality gate that vets and improves plan
- `ca-maestro-junior-dev-doer` (agent, Haiku) - Junior implementer (difficulty 1-3)
- `ca-maestro-dev-doer` (agent, Sonnet) - Standard implementer (difficulty 4-6)
- `ca-maestro-senior-dev-doer` (agent) - Complex task specialist (difficulty 7+)
- `ca-maestro-frontend-dev-doer` (agent) - UI/UX specialist
- `ca-maestro-devops-dev-doer` (agent) - Infrastructure specialist
- `ca-maestro-task-validator` (agent, Haiku) - Strict pass/fail gate (difficulty 1-5)
- `ca-maestro-senior-task-validator` (agent, Sonnet) - Strict pass/fail gate (difficulty 6+)
- `ca-maestro-ui-validator` (agent, Opus) - Visual validation specialist (frontend tasks, difficulty 4+)

**How It Works**:

Maestro executes **Phases 1-7** with continuous execution between user checkpoints:

| Phase | Name | What Happens | User Checkpoint? |
|-------|------|-------------|------------------|
| 1 | Initialize | Fetch story, create branch, create context files | No |
| 2 | Scout | Research codebase patterns, conventions, test coverage | No |
| 3 | Questions | Present scout's ambiguities to user for answers | Yes (if ambiguities exist) |
| 4 | Plan | Break story into tasks with difficulty/type/TDD structure | No |
| 5 | Review | Quality gate: plan-reviewer vets and improves the plan | No |
| 6 | Approve | User reviews and approves the plan | Yes |
| 7 | Develop | Implement tasks one-by-one with mandatory validation | Yes (only on blocker) |

**Agent Roster**:

| Agent | Model | Role |
|-------|-------|------|
| `ca-maestro-scout` | Opus | Codebase researcher — analyzes patterns, conventions, test coverage |
| `ca-maestro-planner` | Opus | Task decomposer — breaks story into tasks with difficulty/type tags |
| `ca-maestro-plan-reviewer` | Opus | Quality gate — vets and improves plan before user sees it |
| `ca-maestro-junior-dev-doer` | Haiku | Junior implementer — handles difficulty 1-3 tasks |
| `ca-maestro-dev-doer` | Sonnet | Standard implementer — handles difficulty 4-6 tasks |
| `ca-maestro-senior-dev-doer` | Opus | Complex task specialist — handles difficulty 7+ and escalations |
| `ca-maestro-frontend-dev-doer` | Opus | UI/UX specialist — handles `[Type: frontend]` tasks at any difficulty |
| `ca-maestro-devops-dev-doer` | Opus | Infrastructure specialist — handles `[Type: devops]` tasks at any difficulty |
| `ca-maestro-task-validator` | Haiku | Strict pass/fail gate — validates difficulty 1-5 tasks |
| `ca-maestro-senior-task-validator` | Sonnet | Strict pass/fail gate — validates difficulty 6+ tasks |
| `ca-maestro-ui-validator` | Opus | Visual validation specialist — browser screenshots + interaction testing for frontend tasks |

**Routing Rules**:

Tasks are routed using two-dimensional routing:

1. **Type tag** (checked first):
   - `[Type: frontend]` → `ca-maestro-frontend-dev-doer` (regardless of difficulty)
   - `[Type: devops]` → `ca-maestro-devops-dev-doer` (regardless of difficulty)

2. **Difficulty rating** (fallback for untagged tasks):
   - Difficulty 7+ → `ca-maestro-senior-dev-doer`
   - Difficulty 4-6 → `ca-maestro-dev-doer`
   - Difficulty 1-3 → `ca-maestro-junior-dev-doer`

**Failure Handling**:
- Specialist tasks (frontend/devops) retry with the same specialist (no cross-agent escalation)
- Junior tasks (difficulty 1-3) escalate: junior → dev-doer → senior-dev-doer
- Standard tasks (difficulty 4+) escalate: same agent → senior-dev-doer
- Development halts after 3 failures on any single task — user decides next step

**File Organization**:

Maestro creates a `.maestro/` directory at project root with three files per story:

```
.maestro/
  context-{STORY-ID}.md    # Status dashboard — where things stand now
  todo-{STORY-ID}.md       # Task list with difficulty/type tags
  diary-{STORY-ID}.md      # Narrative log — how we got here
  demo/                    # Demo artifacts (if frontend tasks produce them)
```

**Context File**: Single source of truth. Contains Story Details, Current Status, Research Findings, Task Progress, Agent Outputs, Blockers, Decisions.

**Diary File**: Narrative log of discoveries, decisions, problems, and successes. Agents read before starting work and write when they discover something that could affect later work. Uses grep-able tags: `[decision]`, `[problem]`, `[learning]`, `[success]`.

**Todo File**: Task list created by planner with difficulty ratings, type tags, implementation notes, and success criteria.

**Resume Capability**:

Maestro can resume from where it left off. It reads the "Current Status" section of the context file to determine which phase to resume from. If no context file exists, starts fresh.

**Visual Verification**:

For stories with UI components, Maestro can use browser automation (Playwright MCP or Claude Code browser integration) during Phase 7 to verify that implemented UI actually looks and interacts correctly. If problems are found, new fix tasks are created automatically.

**Usage**:
```bash
# Jira ticket
/arc-maestro JIRA-123

# File-based story
/arc-maestro ./stories/my-story.md
/arc-maestro .stories/implement-auth.md

# Resume interrupted session (reads context file)
/arc-maestro JIRA-123
```

**Example Flow**:
```
User: /arc-maestro JIRA-456

Phase 1: Initialize
✓ Fetched story from Jira
✓ Created branch: feature/JIRA-456-add-export
✓ Created .maestro/ directory with context, diary, todo files

Phase 2: Scout
✓ Researched codebase patterns
✓ Analyzed test coverage
✓ Documented findings in context file

Phase 3: Questions (if needed)
? Scout has 2 ambiguities — need your input

Phase 4: Plan
✓ Created 12-task plan with difficulty ratings

Phase 5: Review
✓ Plan-reviewer improved plan (added security tasks, fixed TDD requirements)

Phase 6: Approve
[Presents plan to user]
? Approve plan? (yes/no/changes)

Phase 7: Develop
✓ Task 1/12: [dev-doer] Create user model [Difficulty: 3/10] — COMPLETE
✓ Task 2/12: [dev-doer] Add validation layer [Difficulty: 4/10] — COMPLETE
✓ Task 3/12: [senior-dev-doer] Implement OAuth flow [Difficulty: 8/10] — COMPLETE
...
✓ All tasks complete
✓ Staged changes
✓ Committed: "JIRA-456: Add export functionality"
✓ Pushed to remote

Ready for code review. Run: /arc-maestro-review JIRA-456
```

---

#### `/arc-maestro-review` - Code Review and PR Creation

**Purpose**: Executes the final 3 phases of the Maestro pipeline — code review, bug fixes with regression tests, and PR creation. Always starts fresh from Phase 8.

**Powered by** (in execution order):
- `ca-maestro-code-review` (agent) - Two-pass reviewer with enhanced bug-finding
- `ca-maestro-code-review-responder` (agent) - Addresses vetted concerns, fixes bugs
- `ca-code-review-validator` (agent, existing) - Batch validates review feedback items

**How It Works**:

Maestro-review executes **Phases 8-10**:

| Phase | Name | What Happens |
|-------|------|-------------|
| 8 | Code Review | Two-pass review: generate concerns then batch-vet |
| 9 | Respond | Fix bugs with regression tests, address other concerns |
| 10 | Complete | Commit review fixes, push, create PR |

**Phase 8 — Code Review**:
- **Pass 1**: Generate concerns across all dimensions (testing, data layer, performance, bugs, security, frontend, code quality, integration)
- **Enhanced bug-finding**: Executable failure paths, tri-state logic detection, framework contract verification, boolean expression substitution
- **Line number verification**: Read actual files at cited lines, quote actual code
- **Pass 2**: Batch validate all concerns via `ca-code-review-validator`, categorize as KEEP/REMOVE/CLARIFY

**Phase 9 — Respond**:
- **Bugs first**: Understand failure path, implement minimal fix, add regression test (if code has test coverage)
- **Other concerns**: Process via decision tree (critical → FIX, objectively wrong → FIX, quick fix → FIX, time-consuming → DOCUMENT, out-of-scope → DOCUMENT, style preference → DISMISS)
- **Final verification**: All tests pass, no skipped tests, linting clean

**Phase 10 — Complete**:
- Commit review fixes
- Push to remote
- Create PR via `gh pr create` with generated summary and test plan
- Display PR URL

**Usage**:
```bash
# Explicit story ID
/arc-maestro-review JIRA-456

# Auto-detect (uses most recent context file)
/arc-maestro-review
```

**Example Flow**:
```
User: /arc-maestro-review JIRA-456

Phase 8: Code Review
✓ Pass 1: Generated 8 concerns
✓ Pass 2: Validated concerns (5 KEEP, 2 REMOVE, 1 CLARIFY)
✓ Stored vetted review in context file

Phase 9: Respond
✓ BUG 1: Fixed null pointer in export logic (added regression test)
✓ BUG 2: Fixed race condition in async handler (added regression test)
✓ Concern 3: Refactored error handling (material improvement)
✓ Concern 4: Documented performance consideration (out of scope for this PR)
✓ Concern 5: Dismissed style preference
✓ All tests pass (124 passed, 0 skipped)

Phase 10: Complete
✓ Committed: "JIRA-456: Address code review feedback"
✓ Pushed to feature/JIRA-456-add-export
✓ Created PR: https://github.com/owner/repo/pull/789

Ready for human review!
```

---

### Skills

#### `/rubber-duck` - Trusted Peer Developer

**Purpose**: A conversational sounding board for when you want to talk through a technical idea, design, or plan. Acts as a trusted peer who wants your idea to succeed — not a rubber stamp, not a blocker.

**How It Works**:

The conversation flows through natural phases:

1. **Listen and Understand** — Lets you explain your idea, restates it to confirm understanding, asks one clarifying question at a time. Stays here until both the problem and your approach are clear.
2. **Explore Together** — Probes assumptions, edge cases, and failure modes. Asks "what happens when..." questions. Only explores alternatives after understanding why you chose this approach.
3. **Strengthen** — Suggests specific improvements one at a time. Points out risks, asks about testing and rollback plans.
4. **Summarize** — Only when asked or when the conversation wraps naturally. Recaps strengths, open concerns, decisions made, and remaining unknowns.

**Key behaviors**:
- One question or concern per response — never a wall of feedback
- Understands before suggesting — won't offer alternatives until it grasps the problem and your thinking
- Uses codebase research to verify claims instead of speculating
- Direct but constructive — names problems plainly, frames concerns as questions

**Usage**:
```bash
# Start a conversation
/rubber-duck

# With context
/rubber-duck I'm thinking about replacing our REST API with GraphQL
```

---

## Notes

This project assumes that `.*.md` files (dot-prefixed markdown files) are gitignored in your projects. Working files and temporary documentation generated by these commands will use this naming pattern to avoid cluttering your repository.

Add this to your `.gitignore`:
```
/.*.md
```

## License

MIT License - See LICENSE file for details.
