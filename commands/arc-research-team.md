---
description: Team-based parallel deep research — decomposes complex questions into threads investigated by parallel researcher agents, then synthesizes into a cohesive report
allowed-tools: "*"
---

# Arc Research Team - Parallel Deep Research

Research question: {{args}}

This command orchestrates a team of parallel researcher agents to investigate complex, multi-faceted research questions. It decomposes the question into independent threads, dispatches researchers to investigate in parallel, and synthesizes findings into a cohesive report.

```
Decompose (lead) -> Investigate (3x ca-research-agent, parallel) -> Synthesize (ca-research-synthesizer) -> Cleanup
```

### When to Use This vs arc-deep-research

| Use arc-deep-research when... | Use arc-research-team when... |
|-------------------------------|-------------------------------|
| Single focused question | Multi-faceted question with 3+ independent threads |
| Depth over breadth | Breadth over depth |
| Token-efficient | Speed-efficient (parallel investigation) |
| "How does X work?" | "How does X work across systems A, B, and C?" |

---

## PHASE 1: Decompose

### Step 1.1: Parse the Research Question

Extract the research question from `$ARGUMENTS` or from conversation context if no arguments provided.

If the question is too vague or broad to decompose, ask the user to clarify before proceeding.

### Step 1.2: Decompose into Threads

Break the research question into **3-6 independent research threads**. Each thread should be:
- **Independent**: Can be investigated without knowing results of other threads
- **Specific**: Clear enough that a researcher knows exactly what to look for
- **Bounded**: Has a defined scope that won't spiral into unlimited investigation
- **Valuable**: Contributes meaningfully to answering the overall question

For each thread, write:
- **Title**: Short descriptive name
- **Question**: The specific question to investigate
- **Starting points**: Suggested files, search terms, or areas to begin
- **Scope**: What's in and out of bounds

### Step 1.3: Show Decomposition to User

Display the decomposition:

```markdown
## Research Decomposition: [Topic]

I've broken this into [N] independent research threads:

1. **[Thread Title]** — [Brief description]
2. **[Thread Title]** — [Brief description]
3. **[Thread Title]** — [Brief description]
[...]

Spawning 3 researchers to investigate these in parallel...
```

### Step 1.4: Create Team and Tasks

1. **TeamCreate** with `team_name` based on the research topic (e.g., `research-auth-flow`)
2. **TaskCreate** for each research thread with:
   - `subject`: Thread title
   - `description`: Full thread details (question, starting points, scope)
   - `activeForm`: "Investigating [thread title]"
3. Spawn **3** `ca-research-agent` instances using the Task tool:
   - `subagent_type`: `ca-research-agent`
   - `team_name`: the team name from step 1
   - Names: `researcher-1`, `researcher-2`, `researcher-3`
   - Each agent's prompt should include the overall research question for context
   - Run all 3 in background using `run_in_background: true`

---

## PHASE 2: Investigate

### Step 2.1: Monitor Progress

As researchers send messages with their findings:
- Track which threads are complete
- Report brief progress to the user (e.g., "Thread 2 of 5 complete: [title]")
- Collect all findings for the synthesis phase

### Step 2.2: Manage Follow-ups

Researchers may create follow-up tasks via TaskCreate. Monitor the task list:
- **Enforce 12-task cap**: If researchers approach the limit, send a message asking them to prioritize existing tasks over creating new ones
- **Watch for scope creep**: If follow-up tasks diverge from the original question, note this for the user

### Step 2.3: Handle Completion

When all tasks are complete (check TaskList):
- Collect all findings from researcher messages
- Proceed to Phase 3

If researchers get stuck or a task takes too long:
- Send a message asking for a status update
- Consider whether the thread should be abandoned or simplified

---

## PHASE 3: Synthesize

### Step 3.1: Compile Findings

Gather all researcher findings into a single document. For each completed thread:
- Include the full structured findings from the researcher's message
- Note the confidence level
- Include all citations

### Step 3.2: Spawn Synthesizer

Use the Task tool to spawn `ca-research-synthesizer`:
- `subagent_type`: `ca-research-synthesizer`
- `team_name`: the team name
- `name`: `synthesizer`
- Prompt must include:
  - The original research question
  - All compiled findings from researchers
  - Any notes about follow-up threads or scope changes

### Step 3.3: Present Report

When the synthesizer returns its report:
- Display the full report to the user
- The report should stand on its own as a comprehensive answer

---

## PHASE 4: Cleanup

### Step 4.1: Shutdown Team

1. Send `shutdown_request` to all researchers (`researcher-1`, `researcher-2`, `researcher-3`)
2. Send `shutdown_request` to `synthesizer`
3. Wait for shutdown confirmations
4. **TeamDelete** to clean up team and task resources

### Step 4.2: Follow-up Options

After presenting the report, offer the user next steps:

```markdown
---

**Follow-up options:**
- Ask me to dig deeper into any specific finding
- Run `/arc-deep-research` on a specific thread for more depth
- Ask clarifying questions about the report
```

---

## Implementation Notes

### Why 3 Researchers

Three researchers provides good parallelism for 4-8 tasks without excessive token cost. With a shared task list, researchers naturally load-balance — faster threads complete first and the researcher picks up the next available task.

### Task Cap (12 Maximum)

The 12-task cap (2x the maximum initial thread count of 6) prevents unbounded task creation spirals. Researchers can create follow-ups, but the cap keeps the investigation focused.

### Researcher Isolation

Researchers work independently and communicate only with the team lead (not with each other). This prevents:
- Groupthink and confirmation bias
- One researcher's incorrect finding contaminating others
- Complex coordination overhead

The synthesizer is responsible for resolving contradictions, not the researchers.

### Error Handling

- If a researcher fails or becomes unresponsive, note the incomplete thread and proceed with available findings
- If fewer than half the threads complete, warn the user that the report may be incomplete
- If the synthesizer fails, present raw researcher findings directly with a note that synthesis was not performed

### Token Cost Warning

This command spawns 4-5 agents (3 researchers + synthesizer + lead coordination). It consumes significantly more tokens than single-agent research. Use `arc-deep-research` for simpler questions where parallel investigation isn't needed.

### No Ultrathink

Neither ca-research-agent nor ca-research-synthesizer use extended thinking. This workflow prioritizes breadth-first investigation and efficient parallel execution over deep analytical reasoning.

---

## Example User Experience

```
User: /arc-research-team How does the plugin system work in this repository?

Claude: ## Research Decomposition: Plugin System

I've broken this into 5 independent research threads:

1. **Plugin Manifest & Metadata** — How plugin.json and marketplace.json define and describe plugins
2. **Installation Mechanism** — How plugins are installed and loaded by Claude Code
3. **Command & Agent Registration** — How plugin commands and agents become available
4. **File Structure & Conventions** — Required directory layout and naming patterns
5. **Distribution & Marketplace** — How plugins are published and discovered

Spawning 3 researchers to investigate these in parallel...

[Progress updates as threads complete]

Thread 1 of 5 complete: Plugin Manifest & Metadata
Thread 2 of 5 complete: File Structure & Conventions
Thread 3 of 5 complete: Installation Mechanism
Thread 4 of 5 complete: Command & Agent Registration
Thread 5 of 5 complete: Distribution & Marketplace

All threads complete. Synthesizing findings...

# Research Report: Plugin System
[Full synthesized report]

---
Follow-up options:
- Ask me to dig deeper into any specific finding
- Run /arc-deep-research on a specific thread for more depth
- Ask clarifying questions about the report
```
