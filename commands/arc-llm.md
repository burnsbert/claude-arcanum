# Generate LLM Consultation Prompt

This is a top-level user-facing command that creates a comprehensive, self-contained prompt suitable for copy-pasting into another LLM (Google Gemini, ChatGPT, etc.) to get help with the current problem.

## Instructions

This command runs in two phases:

### Phase 1: Generate Problem Context

1. **Check if a problem context file already exists** in the current directory (`.problem.*.md`)
   - If the user provided a specific problem file, use that
   - If multiple exist, ask which one to use
   - If none exist, invoke the `/ca-store-problem-context` command to create one

### Phase 2: Transform to Self-Contained Prompt

Transform the problem context file into a standalone prompt that does NOT assume filesystem access. This requires:

1. **Read all referenced files** mentioned in the problem context
   - For each file:line reference, read the relevant sections
   - Include enough surrounding context (usually 10-20 lines before/after)
   - Include complete function/class/component definitions when referenced

2. **Gather architectural context**
   - Read key configuration files (package.json, tsconfig.json, etc.)
   - Identify the framework/libraries being used
   - Understand the project structure

3. **Create the self-contained prompt** with this structure:

```markdown
# Problem Consultation Request

I need help solving a problem in my [framework/language] project. Below is all the relevant context.

## Problem Description

[Extract from problem.md - what's wrong, what should happen vs what is happening]

## Project Context

**Framework/Stack**: [e.g., React 18 + TypeScript + Vite]
**Key Dependencies**: [list relevant dependencies with versions]
**Project Structure**:
```
[Brief overview of relevant directory structure]
```

## Relevant Code

### [Filename 1]
```[language]
[Include relevant code sections with line numbers as comments]
// Lines 10-45
[code block]
```

**Context**: [Brief explanation of what this file does and why it's relevant]

### [Filename 2]
```[language]
// Lines 23-67
[code block]
```

**Context**: [Brief explanation]

[Continue for all relevant files]

## What's Been Tried

[Extract from problem.md - approaches that have been attempted]

1. [Attempt 1]
   - What was done
   - Result

2. [Attempt 2]
   - What was done
   - Result

## Error Messages / Symptoms

```
[Include full error messages, stack traces, or describe unexpected behavior]
```

## Questions

[Extract from problem.md - specific questions to ask]

1. [Question 1]
2. [Question 2]
3. [Question 3]

## Additional Context

[Any other relevant information that would help diagnose the problem]

---

Please analyze this problem and provide:
1. Your assessment of what's likely causing the issue
2. Specific steps to resolve it
3. Any potential pitfalls or related issues to watch out for
```

### Output Instructions

After generating the prompt:

1. **Display the prompt** directly to the user in a code block
2. **Provide instructions**:
   ```
   Generated LLM consultation prompt (copy the text below):

   This prompt is self-contained and ready to copy-paste into:
   - Google Gemini (gemini.google.com)
   - ChatGPT (chat.openai.com)
   - Claude (claude.ai)
   - Any other LLM interface

   The prompt includes all necessary code context and does not require
   filesystem access. Simply copy the entire prompt and paste it
   into your LLM of choice.
   ```

## Important Guidelines

### Code Inclusion Strategy

**DO include**:
- Complete function/method definitions that are mentioned in the problem
- Relevant class definitions and their key methods
- Configuration files in full if they're small (<50 lines)
- Error-producing code sections with 10-20 lines of context
- Import statements and dependencies

**DON'T include**:
- Entire large files (>200 lines) - extract only relevant sections
- Test files unless the problem is specifically about tests
- Generated code or build artifacts
- Third-party library code (just mention the library version)

### Context Balance

- Aim for 200-500 lines of total code across all snippets
- If a critical file is >100 lines, include a summary + the most relevant sections
- Always include line numbers as comments so the user can reference back
- Group related code sections together

### Formatting

- Use proper markdown code fences with language identifiers
- Use clear section headers
- Keep the prompt readable and scannable
- Put the most critical code sections first

### Problem Clarity

- Make sure the problem description is clear and standalone
- Don't assume the other LLM has any context beyond what's in the prompt
- Include concrete symptoms, not just "it doesn't work"
- Be specific about what was expected vs what happened

## Example Usage Scenario

User is debugging a React component rendering issue:

1. They run `/arc-llm` in Claude Code
2. Command sees no `.problem.*.md` file exists
3. Command invokes `/ca-store-problem-context` which creates `.problem.20250108-095522.md`
4. Command reads that problem file and identifies:
   - Main component: `src/components/UserProfile.tsx`
   - Related hook: `src/hooks/useUserData.ts`
   - Type definitions: `src/types/user.ts`
   - Error mentions line 45 of UserProfile.tsx
5. Command reads these files and extracts:
   - Full UserProfile component (60 lines)
   - Full useUserData hook (30 lines)
   - User type definition (15 lines)
   - package.json to identify React version
6. Command generates comprehensive prompt with all code included
7. Displays the prompt to user in a code block with instructions

User can now copy-paste the entire prompt into Gemini or ChatGPT.

## Technical Notes

- Use the Read tool extensively to gather code
- Use Grep to find related code if references are incomplete
- Use Glob to understand project structure
- Be smart about what code is essential vs nice-to-have
- When in doubt, include more context rather than less
- The prompt should be comprehensive enough that the other LLM can provide actionable advice without asking follow-up questions about code content
