# Store Problem Context

You are helping the user document the problem they're currently stuck on. This command is invoked during an active Claude Code session where you already have full context about what the user has been working on.

## Instructions

**Extract the problem from the current conversation context** - Analyze:
- What the user has been trying to accomplish
- What files have been discussed, read, or modified
- What errors or issues have been encountered
- What approaches have been tried
- Where you/they are currently stuck

**Gather relevant context** by examining:
- Current working directory and git status
- Recently modified files (git diff, git status)
- Files that have been referenced in the current session
- Any error messages or test failures from the conversation
- Project structure and configuration files if relevant

**Create a `.problem.[uniqid].md` file** where `[uniqid]` is a unique identifier (use timestamp format like `YYYYMMDD-HHMMSS` or similar).

## File Format

The .problem.[uniqid].md file should be structured as a detailed prompt to an LLM, including:

### Header Section
- **Date/Time**: When the problem was documented
- **Project**: Project name/directory
- **Status**: Current git branch and working tree status

### Problem Description
- Clear statement of the problem
- What the user is trying to accomplish
- What's currently happening vs. what should happen
- Any error messages or unexpected behavior

### Context
- **Relevant Files**: List key files involved (with paths and relevant line numbers)
  - Format: `path/to/file.ext:line_number` - brief description
- **Recent Changes**: Summary of recent git changes if relevant
- **Dependencies**: Relevant dependencies, frameworks, or tools involved
- **Environment**: Any relevant environment details

### Investigation So Far
- What has been tried already (extract from conversation history)
- What debugging steps have been taken
- Any theories or hypotheses about the cause
- What tools/approaches were used (searches, edits, tests, etc.)

### Code References
- Include brief code snippets ONLY when essential for understanding
- Otherwise, just reference file:line_number since the consumer has filesystem access
- Use relative paths from project root

### Questions for LLM
- Specific questions the user wants answered
- Areas where guidance is needed

## Example Output Format

```markdown
# Problem: [Brief Title]

**Date**: YYYY-MM-DD HH:MM:SS
**Project**: /path/to/project
**Branch**: main
**Status**: clean / modified files

## Problem Description

[Detailed description of the problem]

## Context

### Relevant Files
- `src/components/Widget.tsx:45-67` - Component that's failing to render
- `src/utils/helper.ts:23` - Utility function being called
- `package.json` - Dependencies

### Recent Changes
- Modified Widget.tsx to add new prop
- Updated helper function signature

### Environment
- React 18.2.0
- TypeScript 5.0
- Node 18.x

## Investigation So Far

- Tried [approach 1]
- Verified [thing 2]
- Noticed [observation 3]

## Questions

1. Why is [specific behavior] happening?
2. What's the best approach to [solve X]?
3. Are there any known issues with [Y]?
```

## Important Notes

- **The user does not need to provide any information** - Extract everything from the current conversation context
- Synthesize all the information that has been discussed in the session
- Keep the file concise but comprehensive
- Since the consumer has filesystem access, avoid quoting large blocks of code
- Use file references (path:line_number) instead
- Include enough context for someone unfamiliar with the project to understand
- Make it easy to pick up the problem later or share with another LLM
- Save the file in the project root directory
- Do NOT commit this file to git (it should be in .gitignore pattern `/.problem.*.md`)
- After creating the file, tell the user the filename and give them a brief summary of what was documented
