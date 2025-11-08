# Investigate Problem - Automated Troubleshooting Workflow

This is a top-level orchestration command that runs a complete troubleshooting workflow: capturing the problem, generating theories, validating each theory, and presenting ranked next steps.

## Workflow Overview

```
1. Document Problem → 2. Generate Theories → 3. Validate Each Theory → 4. Rank & Present Options
   (ca-store-problem-context)  (ca-brainstormer)      (ca-problem-theory-validator × N)
```

## Instructions

### Phase 1: Create Problem Context

1. **Check for existing problem context file** (`.problem.*.md`)
   - If user provided a specific file, use that
   - If multiple exist, ask which one to use
   - If none exist, invoke `/ca-store-problem-context` to create one

2. **Confirm the problem context** with the user:
   ```
   Using problem context: .problem.[timestamp].md

   Problem: [Brief summary from the file]

   Ready to investigate? This will:
   - Generate 5-6 theories about the cause
   - Validate each theory through code investigation
   - Provide ranked next steps

   Proceed? (yes/no)
   ```

### Phase 2: Generate Theories

3. **Invoke the ca-brainstormer agent** with the problem context file
   - Use the Task tool with "ultrathink" at the start of the prompt for deep analysis
   - Example prompt: "ultrathink\n\nAnalyze the problem context in .problem.[timestamp].md and generate 5-6 theories..."
   - Wait for the agent to complete its investigation
   - The agent will return 5-6 theories ordered by likelihood
   - Extract the list of theories from the agent's output

4. **Present theories to user**:
   ```
   Generated [N] theories. Now validating each one...

   1. [Theory 1 title] (Likelihood: High)
   2. [Theory 2 title] (Likelihood: High)
   3. [Theory 3 title] (Likelihood: Medium)
   4. [Theory 4 title] (Likelihood: Medium)
   5. [Theory 5 title] (Likelihood: Low)
   ```

### Phase 3: Validate Theories in Parallel

5. **Launch multiple ca-problem-theory-validator agents** - one for each theory
   - Use the Task tool to launch agents IN PARALLEL (single message with multiple Task calls)
   - Example prompt: "Validate theory #1 from .problem.[timestamp].md: [theory description]..."
   - Each agent gets the problem context file + one specific theory to validate
   - This is the most time-consuming phase but parallelization makes it efficient

6. **Wait for all validation agents to complete**
   - Collect results from each validator agent
   - Each will return: PROVEN / DISPROVEN / UNCERTAIN + evidence + next steps

### Phase 4: Synthesize Results

7. **Process validation results** into a ranked action plan:

   **For each validation result, extract**:
   - Theory title
   - Status (PROVEN / DISPROVEN / UNCERTAIN)
   - Key evidence (supporting/contradicting)
   - Recommended next steps

   **Create prioritized categories**:

   **A. PROVEN Theories** (These are the root causes - fix these first!)
   - List each proven theory with fix steps

   **B. HIGH CONFIDENCE Theories** (Uncertain but strong supporting evidence)
   - List theories with mostly supporting evidence
   - Include verification steps needed

   **C. WORTH INVESTIGATING** (Uncertain with mixed evidence)
   - List theories that need more data
   - Include data-gathering steps

   **D. RULED OUT** (Disproven theories)
   - List for completeness, no action needed

8. **Present the synthesized results**:

```markdown
# Investigation Results

## Summary
Investigated [N] theories. Found:
- [X] PROVEN root causes
- [Y] high-confidence possibilities
- [Z] theories needing more data
- [W] theories ruled out

---

## 🔴 PROVEN Root Causes

### [Theory Title]

**Evidence**:
- [Key supporting evidence from validator]
- [More evidence]

**How to Fix**:
1. [Specific action step]
2. [Specific action step]
3. [Verification step]

---

## 🟡 High Confidence (Needs Verification)

### [Theory Title]

**Evidence**:
- [Supporting evidence]
- [Missing information that would confirm]

**Next Steps to Verify**:
1. [Specific investigation or test]
2. [What to look for]

---

## 🟢 Worth Investigating

### [Theory Title]

**Why This Might Be It**:
- [Reasoning]

**How to Check**:
1. [Investigation step]

---

## ⚫ Ruled Out

### [Theory Title]
**Why it's not the cause**: [Brief explanation]

---

## Recommended Action Plan

Based on the investigation, here's what to do next:

**Immediate Actions** (if any theories proven):
1. [Fix for proven theory 1]
2. [Fix for proven theory 2]

**If no proven causes**, try these in order:
1. [Verification step for highest confidence theory]
2. [Verification step for next theory]
3. [Investigation for other theories]

```

9. **Ask the user what they want to do**:

```
What would you like to do?

1. Implement fix for [proven theory / top theory]
2. Run verification steps for [high confidence theory]
3. Investigate [uncertain theory] further
4. Generate an LLM prompt for external consultation (/arc-llm)
5. Show me the full details from a specific theory validation
6. Something else (please specify)
```

## Important Implementation Notes

### Extended Thinking
- **CRITICAL**: Always include "ultrathink" at the start of ca-brainstormer prompts for deep analysis
- This enables extended thinking mode (~32K token budget) for complex reasoning

### Parallel Execution
- **CRITICAL**: Launch all validator agents in parallel using a single message with multiple Task tool calls
- Example: If there are 5 theories, send ONE message with 5 Task tool invocations
- This dramatically reduces total time (from 5× sequential to 1× parallel)

### Error Handling
- If a validator agent fails, note it in the results but continue with others
- If the brainstormer finds fewer than 3 theories, that's fine - validate what we have
- If all theories are disproven, that's valuable information - suggest running `/arc-llm` for external help

### Context Management
- The problem context file is the source of truth
- All agents receive the same problem context file path
- Don't regenerate the problem context between phases unless explicitly requested

### User Interaction
- Keep the user informed at each phase
- Show progress: "Validating theory 1 of 5..."
- Don't make the user wait in silence - explain what's happening
- At the end, offer clear options for next steps

### Synthesis Quality
- Don't just repeat what the validators said - synthesize insights
- Look for patterns across multiple theories
- If multiple theories point to the same area, call that out
- Rank actions by: (1) Proven fixes first, (2) Highest evidence theories, (3) Easiest to verify

### No Output File Needed
- Display the investigation results directly to the user
- The `.problem.[timestamp].md` already has the problem context
- If user wants to share externally, they can use `/arc-llm`

## Example User Experience

```
User: /arc-investigate

Claude: I'll investigate the current problem systematically.

First, let me document the problem context...
Created: .problem.20250108-103045.md

Problem: React component not re-rendering when state changes

Ready to investigate? This will:
- Generate 5-6 theories about the cause
- Validate each theory through code investigation
- Provide ranked next steps

Proceed?

User: yes

Claude: Generating theories...

Generated 5 theories:
1. Missing key prop in list rendering (Likelihood: High)
2. State mutation instead of immutable update (Likelihood: High)
3. Stale closure in useEffect (Likelihood: Medium)
4. React.memo blocking re-renders (Likelihood: Medium)
5. Incorrect dependency array (Likelihood: Low)

Now validating each theory in parallel...

[Agents run in parallel - takes 1-2 minutes]

# Investigation Results

## Summary
Investigated 5 theories. Found:
- 1 PROVEN root cause
- 1 high-confidence possibility
- 2 theories needing more data
- 1 theory ruled out

## 🔴 PROVEN Root Causes

### State Mutation Instead of Immutable Update

**Evidence**:
- Line 45 of TaskList.tsx directly modifies state array: `tasks.push(newTask)`
- React requires immutable updates to detect changes
- Confirmed in React docs and component behavior matches symptoms

**How to Fix**:
1. Change `tasks.push(newTask)` to `setTasks([...tasks, newTask])`
2. Review other state updates in the file for similar issues
3. Re-test the component to verify re-rendering works

## 🟡 High Confidence (Needs Verification)

### Missing Key Prop in List Rendering

**Evidence**:
- Each <Task> component in map() lacks a key prop
- React warning in console: "Each child in list should have unique key prop"
- This can cause rendering issues but doesn't fully explain the symptoms

**Next Steps to Verify**:
1. Add unique key prop to each <Task> element
2. Check if this resolves any residual rendering issues after the main fix

## Recommended Action Plan

**Immediate Action**:
1. Fix the state mutation in TaskList.tsx:45
   - Change direct mutation to immutable update
   - Test to verify re-rendering works

**Follow-up**:
2. Add key props to list items to eliminate React warnings
3. Run full test suite to catch any similar issues elsewhere

---

What would you like to do?

1. Fix the proven state mutation issue in TaskList.tsx
2. Show me the verification steps for the key prop theory
3. Generate an LLM prompt for external consultation
4. Something else

User: 1

Claude: I'll fix the state mutation issue...
[Proceeds with the fix]
```

## Tips for Effective Investigations

- If all theories are uncertain or disproven, consider:
  - Running `/arc-llm` to get external perspective
  - Re-running with more specific problem description
  - Checking if the problem description accurately captures the symptoms

- If you have too many theories (>6), the brainstormer should filter to the most likely

- If theories overlap significantly, combine them in the synthesis phase

- Always save the investigation results - they're valuable even if you don't fix the issue immediately
