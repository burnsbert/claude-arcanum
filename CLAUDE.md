# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Arcanum is a collection of custom commands and agents for Claude Code that enhance debugging and problem-solving workflows. The tools work together to provide systematic troubleshooting, root cause analysis, and external LLM consultation.

## Architecture

### Naming Convention (CRITICAL)

- **arc-*** - User-facing commands and agents (direct use)
- **ca-*** - Utility commands and agents (internal use only)

This distinction is fundamental to the design. Users interact with `arc-*` tools, which internally orchestrate `ca-*` utilities.

### Key Design Principles

1. **Context Extraction**: Commands auto-extract from current session - minimal user input
2. **No Unnecessary Files**: Display output directly, don't create files unless needed for inter-tool communication
3. **Parallel Execution**: arc-investigate validates theories in parallel for speed
4. **Evidence-Based**: All analysis backed by code investigation, not speculation

### File Outputs

**Only one file type is created**: `.problem.[timestamp].md`
- Used as input for other commands/agents
- Contains file:line references (assumes filesystem access)
- Follows `.*.md` gitignore pattern

**Previously removed**:
- `.investigation.[timestamp].md` - Not needed, display directly
- `.llm-prompt.[timestamp].md` - Not needed, display directly

## Tool Relationships

```
arc-investigate:
  1. Calls ca-store-problem-context (creates .problem.md)
  2. Calls ca-brainstormer (generates theories)
  3. Spawns ca-problem-theory-validator × N in parallel
  4. Synthesizes and displays results

arc-rca:
  1. Extracts context from session
  2. Calls arc-root-cause-analyzer agent
  3. Displays results with action options

arc-llm:
  1. Calls ca-store-problem-context (if needed)
  2. Reads all referenced files
  3. Generates self-contained prompt
  4. Displays for copy-pasting
```

## Development Guidelines

### Adding New Commands

1. Determine if it's user-facing (arc-) or utility (ca-)
2. Create command file in `commands/` directory
3. Follow existing format with clear sections:
   - Instructions (what Claude should do)
   - Usage scenarios
   - Output format
   - Important notes
4. Update README with comprehensive documentation

### Adding New Agents

1. Determine if it's user-facing (arc-) or utility (ca-)
2. Create agent file in `agents/` directory
3. Include:
   - Purpose and when to use
   - Investigation protocol
   - Output format
   - Example analyses
4. Update README with examples

### Documentation Standards

- **Be comprehensive**: Include "How It Works", usage examples, when to use
- **Show examples**: Real example sessions with input/output
- **Provide workflows**: Show how tools work together
- **Answer FAQs**: Anticipate user questions

## Testing Notes

Not yet tested in live Claude Code environment. When testing:
- Verify context extraction from sessions works correctly
- Ensure parallel agent invocation in arc-investigate works
- Test with both fixed and unfixed bugs for arc-rca
- Validate arc-llm prompts work well with external LLMs

## Common Patterns

### Auto-extracting from Session

Commands should analyze conversation history for:
- Files that were discussed, read, or modified
- Error messages and symptoms
- What's been tried
- Git commits and changes
- Test results

### Parallel Agent Invocation

Use single message with multiple Task tool calls:
```markdown
[Uses Task tool to spawn 5 validators in parallel]
```

### Status Determination

For arc-rca, determine if bug is fixed by looking for:
- Recent commits in session
- User saying "fixed", "solved", "resolved"
- Tests passing after changes
