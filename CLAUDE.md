# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Arcanum is a collection of custom commands and agents for Claude Code that enhance debugging and problem-solving workflows. The tools provide systematic troubleshooting, root cause analysis, and external LLM consultation.

## Repository Structure

```
claude-arcanum/
├── commands/          # Custom slash commands (arc-*, ca-*)
├── agents/            # Agent definitions (arc-*, ca-*)
├── scripts/           # Installation utilities
└── README.md          # Comprehensive documentation
```

## Architecture & Design Principles

### Naming Convention (CRITICAL)

- **arc-*** - User-facing tools (direct invocation)
- **ca-*** - Utility tools (internal use only)

This is fundamental to the design. Users interact with `arc-*` tools, which orchestrate `ca-*` utilities behind the scenes.

### Core Design Principles

1. **Context Extraction**: Commands auto-extract from current session - minimal user input required
2. **Display Over Files**: Output directly to user; only create files when needed for tool chaining
3. **Parallel Execution**: arc-investigate validates theories in parallel using single message with multiple Task calls
4. **Evidence-Based**: All analysis backed by code investigation, not speculation

### File Management

**Single file type created**: `.problem.[timestamp].md`
- Input format for command/agent chaining
- Contains file:line references (assumes filesystem access)
- Follows `.*.md` gitignore pattern

**Note**: Previously created `.investigation.*.md` and `.llm-prompt.*.md` files were removed - results display directly instead.

## Tool Workflows

### arc-investigate
```
1. ca-store-problem-context → Creates .problem.md
2. ca-brainstormer → Generates 5-6 theories
3. ca-problem-theory-validator × N (parallel) → Validates each theory
4. Synthesizes → Displays ranked results (PROVEN/HIGH CONFIDENCE/WORTH INVESTIGATING/RULED OUT)
```

### arc-rca
```
1. Extract context from session (or use parameter)
2. arc-root-cause-analyzer agent → Git forensics + root cause analysis
3. Display results with action options
```

### arc-llm
```
1. ca-store-problem-context (if needed)
2. Read all referenced files
3. Generate self-contained prompt (200-500 lines)
4. Display for copy-pasting to external LLM
```

## Development Guidelines

### Adding Commands

1. Choose prefix: `arc-` (user-facing) or `ca-` (utility)
2. Create in `commands/` with sections: purpose, instructions, usage, output format, examples
3. Update README.md with comprehensive documentation including "How It Works" and workflows

### Adding Agents

1. Choose prefix: `arc-` (user-facing) or `ca-` (utility)
2. Create in `agents/` with: purpose, investigation protocol, output format, examples
3. Update README.md with usage examples and when to invoke

### Documentation Standards

- Include complete examples with input/output
- Show how tools integrate with each other
- Provide clear "when to use" guidance
- Keep CLAUDE.md focused on architecture, not exhaustive feature lists (that's for README)

## Key Implementation Patterns

### Context Extraction

Commands analyze conversation history for:
- Files discussed, read, or modified (via Read/Edit tool usage)
- Error messages and symptoms
- What's been tried already
- Git operations (commits, diffs)
- Test results

### Extended Thinking for Agents

**For ca-brainstormer only**: Invoke with "ultrathink" keyword for deep theory generation:
- Start Task tool prompts with "ultrathink\n\n..."
- Enables ~32K token thinking budget vs default 4K
- This agent generates initial theories and benefits from extended thinking

### Parallel Agent Invocation

For arc-investigate: Launch all validators in single message with multiple Task tool calls
```markdown
[Launches 5 ca-problem-theory-validator agents in parallel using single message]
```

### Bug Status Determination

For arc-rca, determine if bug is fixed by checking for:
- Recent commits in session (git commit commands)
- User statements ("fixed", "solved", "resolved")
- Tests passing after changes
- Edit tool usage followed by successful test runs

### RCA Report Requirements

The arc-root-cause-analyzer agent MUST include in all reports:
- **Commit hash** of the breaking change
- **Date/time** when bug was introduced
- **Author** of the breaking change
- Full root cause analysis
- Prevention recommendations

Use `git log --format=fuller` or `git show` to extract complete commit metadata.
