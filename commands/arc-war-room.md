---
description: Team-based parallel investigation — brainstorms theories, dispatches parallel investigators, dynamically spawns new investigators for discovered leads, and synthesizes ranked results with next steps
allowed-tools: "*"
---

# Arc War Room - Team-Based Parallel Investigation

Problem context: {{args}}

This command orchestrates a war room for tough problems. It brainstorms theories, dispatches a team of investigators to validate them in parallel, dynamically spins up new investigators when promising leads are discovered, and synthesizes all findings into ranked results with actionable next steps.

```
Problem Context -> Brainstorm (ca-brainstormer) -> War Room (ca-war-room-investigator team, dynamic) -> Synthesize & Present (lead)
```

### When to Use This vs arc-investigate

| Use arc-investigate when... | Use arc-war-room when... |
|-----------------------------|--------------------------|
| Standard debugging session | Intractable or high-stakes problem |
| 5-6 theories, straightforward validation | Theories may reveal new leads during investigation |
| Fixed scope — validate and report | Dynamic scope — pursue discoveries as they emerge |
| Token-efficient | Thoroughness over efficiency |
| Fire-and-forget parallel validation | Persistent team with adaptive investigation |

Both start the same way (problem context + brainstorming). The war room adds a persistent team that can chase new leads dynamically, while arc-investigate validates its initial theories and stops.

---

## PHASE 1: Problem Context

### Step 1.1: Get Problem Context

1. **Check for existing problem context file** (`.problem.*.md`)
   - If user provided a specific file via `$ARGUMENTS`, use that
   - If multiple exist, ask which one to use
   - If none exist, invoke `/ca-store-problem-context` to create one

2. **Show the problem context** and proceed automatically:
   ```
   War Room activated for: [Brief problem summary]

   Phase 1: Documenting problem context ✓
   Phase 2: Brainstorming theories...
   ```

   **DO NOT pause for confirmation** — proceed immediately to Phase 2.

---

## PHASE 2: Brainstorm

### Step 2.1: Generate Theories

Invoke the **ca-brainstormer** agent with the problem context file:
- Use the Task tool with `"ultrathink"` at the start of the prompt for deep analysis
- Prompt: `"ultrathink\n\nAnalyze the problem context in .problem.[timestamp].md and generate 5-6 theories..."`
- Wait for completion

### Step 2.2: Present Theories

Display theories to the user ranked by likelihood:

```markdown
## Theories Generated

1. **[Theory Title]** — Likelihood: High
2. **[Theory Title]** — Likelihood: High
3. **[Theory Title]** — Likelihood: Medium
4. **[Theory Title]** — Likelihood: Medium
5. **[Theory Title]** — Likelihood: Low

Assembling war room — spinning up investigators...
```

---

## PHASE 3: War Room

This is the core of the workflow. A persistent team investigates theories in parallel, with dynamic adaptation as new leads emerge.

### Step 3.1: Create Team and Initial Tasks

1. **TeamCreate** with a descriptive `team_name` (e.g., `war-room-auth-bug`)

2. **TaskCreate** for each theory, ordered by likelihood (highest first):
   - `subject`: Theory title
   - `description`: Full theory details from brainstormer output, plus the problem context file path and a summary of the problem
   - `activeForm`: "Investigating: [theory title]"

3. **Spawn 3 `ca-war-room-investigator` agents**:
   - `subagent_type`: `ca-war-room-investigator`
   - `team_name`: the team name
   - Names: `investigator-1`, `investigator-2`, `investigator-3`
   - Each agent's prompt should include the problem context file path
   - Run all 3 in background with `run_in_background: true`

### Step 3.2: Monitor and Adapt

As investigators send messages with their findings:

**Track results:**
- Record each theory's status (PROVEN / DISPROVEN / UNCERTAIN)
- Collect evidence and citations
- Report brief progress to user: `"Theory 2 of 5 investigated: [title] — DISPROVEN"`

**Handle new discoveries:**
When an investigator reports a NEW DISCOVERY:
1. **Evaluate the lead** — Is it genuinely novel? Does it explain the symptoms?
2. **If promising**: Create a new task via TaskCreate with the discovery details
3. **If the task count is high and investigators are busy**: The existing investigators will pick it up when they finish their current theory
4. **If you need more parallel capacity**: Spawn an additional investigator (up to **5 total max**)
5. **If not promising**: Note it but don't create a task. Inform the investigator.
6. Report to user: `"New lead discovered: [title] — adding to investigation queue"`

**Enforce limits:**
- **Max 10 total tasks** (theories + discovered leads). If approaching the limit, prioritize rather than add more.
- **Max 5 investigators**. Only spawn beyond initial 3 if there are multiple unclaimed tasks AND existing investigators are all busy.

**Handle stalls:**
- If an investigator seems stuck on a task, send a message asking for status
- If a theory is taking too long, consider whether it should be marked UNCERTAIN and moved on

**Open new lines of investigation when initial theories aren't panning out:**

This is critical. Don't just passively wait for all theories to fail. Actively assess the situation as results come in:

1. **Trigger condition**: Once 3+ theories have been investigated and the majority are DISPROVEN or UNCERTAIN with weak evidence, the initial brainstorm may have been off-target.

2. **Reassess**: Review all findings so far — the evidence gathered, patterns in what was ruled out, and any partial clues from UNCERTAIN results. What you've learned from failed theories is valuable signal about where the problem ISN'T, which constrains where it IS.

3. **Generate new theories**: Based on the accumulated evidence (not from scratch), brainstorm 2-3 new theories that:
   - Account for evidence that contradicted the original theories
   - Explore areas the original brainstorm didn't consider
   - Follow partial clues from UNCERTAIN investigations
   - Consider interactions between components that were individually cleared

4. **Inject into the war room**: Create new tasks for the promising theories. Investigators will claim them naturally from the task list. Inform the user: `"Initial theories largely ruled out. Based on what we've learned, opening new lines of investigation: [titles]"`

5. **This can happen more than once** if needed, but respect the 10-task cap. If you're approaching the cap, replace rather than add — drop UNCERTAIN theories with weak evidence to make room for more promising ones.

6. **Don't re-run the brainstormer agent for this.** You (the lead) have the full picture — every investigator report, every piece of evidence, every disproven path. Use that accumulated context to generate targeted theories yourself. The brainstormer doesn't have this context.

### Step 3.3: Completion

When all tasks are complete (check TaskList periodically):
- Collect all findings from investigator messages
- Proceed to Phase 4

If some tasks couldn't be completed:
- Note them as UNCERTAIN in the synthesis
- Proceed with what's available

---

## PHASE 4: Synthesize & Present

The lead (you) synthesizes all findings. No separate synthesizer agent — you've been tracking everything in real-time.

### Step 4.1: Categorize Results

Process all investigator reports into four categories:

**PROVEN** — Definitive evidence confirms this as a root cause
- Include fix steps from the investigator's report
- If multiple theories are proven, they may be related — call that out

**HIGH CONFIDENCE** — UNCERTAIN but with strong supporting evidence
- Include what evidence exists and what's missing
- Provide specific verification steps

**WORTH INVESTIGATING** — UNCERTAIN with mixed or thin evidence
- Include why it's still plausible
- Provide targeted next steps to gather more data

**RULED OUT** — DISPROVEN with contradicting evidence
- Brief explanation of why, for completeness

### Step 4.2: Present Results

```markdown
# War Room Results

## Summary
Investigated [N] theories ([M] original + [K] discovered during investigation). Found:
- [X] PROVEN root causes
- [Y] high-confidence possibilities
- [Z] theories needing more investigation
- [W] theories ruled out

---

## PROVEN Root Causes

### [Theory Title]

**Evidence**:
- [Key evidence with file:line citations]

**How to Fix**:
1. [Specific action step]
2. [Verification step]

---

## High Confidence (Needs Verification)

### [Theory Title]

**Evidence**:
- [Supporting evidence]
- [What's missing]

**To Verify**:
1. [Specific investigation or test]

---

## Worth Investigating

### [Theory Title]

**Why This Might Be It**: [Reasoning]

**How to Check**:
1. [Investigation step]

---

## Ruled Out

### [Theory Title]
**Why**: [Brief explanation]

---

## Cross-Theory Patterns

[If multiple theories point to the same component, configuration, or code area, call it out here. This is insight that individual investigators couldn't provide.]

---

## Recommended Action Plan

**Immediate Actions** (if any theories proven):
1. [Fix for proven theory 1]
2. [Fix for proven theory 2]

**If no proven causes**, try these in order:
1. [Verification for highest confidence theory]
2. [Verification for next theory]
3. [Investigation for uncertain theories]
```

### Step 4.3: Cleanup and Follow-up

1. **Shutdown investigators**: Send `shutdown_request` to all investigators
2. **TeamDelete** to clean up team and task resources
3. **Offer next steps**:

```markdown
---

What would you like to do?

1. Implement fix for [proven/top theory]
2. Run verification steps for [high confidence theory]
3. Investigate [uncertain theory] further
4. Run /arc-llm to get external help on the problem
5. Show full details from a specific theory investigation
6. Something else
```

---

## Implementation Notes

### Why Start with 3 Investigators

Three provides good parallelism for the initial 5-6 theories. With a shared task list, they naturally load-balance. Starting lean avoids wasted tokens if theories are quickly resolved.

### Dynamic Spawning (up to 5)

New investigators are spawned only when:
- A genuinely new lead is discovered
- All existing investigators are busy on tasks
- There are unclaimed tasks waiting

This keeps the team lean but adaptive. Most investigations will use 3; complex ones with many discoveries might use 4-5.

### Manager Synthesis vs Separate Synthesizer

Unlike arc-research-team which uses a dedicated ca-research-synthesizer, the war room lead does synthesis directly. Rationale:
- The lead has been tracking findings in real-time via SendMessage
- Cross-theory pattern detection benefits from having seen each result arrive
- Problem-solving synthesis is different from research synthesis — it needs to produce ranked actionable steps, not a report organized by theme

### Relationship to arc-investigate

arc-war-room is a superset of arc-investigate's capabilities:
- Same Phase 1 (problem context) and Phase 2 (brainstorming)
- Phase 3 replaces fire-and-forget parallel validation with a persistent adaptive team
- Phase 4 replaces static synthesis with dynamic pattern-aware synthesis

Use arc-investigate for routine debugging. Use arc-war-room when the problem is tough enough that you expect investigation to reveal new leads.

### Error Handling

- If an investigator fails or becomes unresponsive, note the incomplete theory as UNCERTAIN
- If the brainstormer produces fewer than 3 theories, that's fine — investigate what you have
- If all theories are DISPROVEN and no new leads emerged, suggest running `/arc-llm` for external help
- If the team gets stuck, inform the user and suggest narrowing the problem description

### Token Cost Warning

This command spawns 3-5 investigators plus uses ca-brainstormer with ultrathink. It consumes significantly more tokens than arc-investigate. Use arc-investigate for standard problems; reserve the war room for intractable or high-stakes issues.

### Ultrathink Usage

- **ca-brainstormer**: YES — invoked with ultrathink for deep theory generation
- **ca-war-room-investigator**: NO — breadth-first investigation, standard thinking is sufficient
- **Lead synthesis**: Standard thinking — synthesis is collation and ranking, not deep analysis

---

## Example User Experience

```
User: /arc-war-room

Claude: War Room activated for: API requests returning 500 errors intermittently after Redis upgrade

Phase 1: Problem context ✓ (.problem.20250208-143022.md)
Phase 2: Brainstorming theories...

## Theories Generated

1. **Redis connection pool exhaustion** — Likelihood: High
2. **Serialization format mismatch after upgrade** — Likelihood: High
3. **TTL behavior change in new Redis version** — Likelihood: Medium
4. **Connection string format incompatibility** — Likelihood: Medium
5. **Race condition in cache invalidation** — Likelihood: Low

Assembling war room — spinning up 3 investigators...

[Investigators work in parallel]

Theory 1 of 5 investigated: Connection string format — DISPROVEN
Theory 2 of 5 investigated: Redis connection pool exhaustion — UNCERTAIN (strong evidence)
New lead discovered: Redis cluster failover causing transient disconnects — adding to investigation queue
Theory 3 of 5 investigated: Serialization format mismatch — PROVEN
Theory 4 of 5 investigated: TTL behavior change — DISPROVEN
Theory 5 of 6 investigated: Race condition in cache invalidation — UNCERTAIN
Theory 6 of 6 investigated: Redis cluster failover — PROVEN

All investigations complete. Synthesizing...

# War Room Results

## Summary
Investigated 6 theories (5 original + 1 discovered). Found:
- 2 PROVEN root causes
- 1 high-confidence possibility
- 2 theories ruled out

## PROVEN Root Causes

### Serialization Format Mismatch
**Evidence**:
- `src/cache/redis-client.ts:67` — using msgpack serialization
- Redis 7.x changed msgpack handling for binary-safe strings
- Error logs show deserialization failures matching 500 errors

**How to Fix**:
1. Update msgpack serializer config in redis-client.ts:67-72
2. Add format version header to cached values
3. Flush existing cache after fix

### Redis Cluster Failover (Discovered During Investigation)
**Evidence**:
- `infrastructure/redis.conf:23` — failover-timeout set to 0ms (was default before upgrade)
- New Redis version treats 0 as "immediate failover" not "disabled"
- Matches intermittent pattern — failovers cause brief disconnects

**How to Fix**:
1. Set failover-timeout to 30000 in redis.conf:23
2. Add connection retry logic in redis-client.ts:12

## Cross-Theory Patterns
Both proven causes relate to Redis version behavior changes that weren't caught in upgrade testing. Recommend adding Redis version-specific integration tests.

---

What would you like to do?
1. Fix the serialization format mismatch
2. Fix the failover timeout configuration
3. Fix both issues
4. Show full investigation details for a specific theory
5. Something else

User: 3
Claude: I'll fix both issues...
```
