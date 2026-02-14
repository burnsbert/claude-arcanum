---
description: Creative ideation workflow — generates, critiques, evolves, and ranks ideas toward a goal through 5 rounds of thinking, vetting, and riffing
allowed-tools: "*"
argument-hint: <goal> [material file paths] [N rounds] | +N
---

# Arc Think Tank - Creative Ideation Workflow

Goal and materials: {{args}}

This command orchestrates a creative think tank that generates, critiques, evolves, and ranks ideas toward a user-provided goal. Multiple rounds of thinking, vetting, and riffing produce a rich set of ideas, which a judge then ranks into a final report.

```
Parse Goal + Materials → N× [Thinker → Vetter → Riffer] → Final Vetter → Judge → Report
```

### Invocation Modes

| Mode | Example | Behavior |
|------|---------|----------|
| **New session (default)** | `/arc-think-tank how do I reduce churn?` | 5 rounds, new session |
| **New session (custom rounds)** | `/arc-think-tank how do I reduce churn? [3 rounds]` | 3 rounds, new session |
| **Add rounds to existing** | `/arc-think-tank +2` | Resume most recent session, run 2 more rounds, re-judge |
| **Bare resume** | `/arc-think-tank` | Resume or start new (interactive) |

---

## PHASE 1: Initialize

### Step 1.1: Parse Arguments

Parse `$ARGUMENTS` to extract four possible components:

1. **Add-rounds token**: If args match `+N` (e.g., `+2`, `+3`) with no other goal text, this is an **add-rounds invocation**. Set `add_rounds = N` and skip to Step 1.3.

2. **Round count token**: If args contain `[N rounds]` (e.g., `[3 rounds]`, `[7 rounds]`), extract N as the round count. Remove it from the args before further parsing. If not present, default to **5 rounds**.

3. **File path tokens**: Any token containing `/`, starting with `./` or `~`, or ending with a known extension (`.md`, `.txt`, `.pdf`, `.json`, `.yaml`, `.yml`, `.csv`, `.html`, `.xml`, `.doc`, `.docx`)

4. **Goal text**: Everything else (concatenated as a sentence)

**If no goal text is found** (and not an add-rounds invocation):
- Say: "Think Tank requires a goal. What would you like to brainstorm about?"
- **WAIT for user response**
- Use their response as the goal

### Step 1.2: Generate Task ID

Generate a task ID using the current timestamp:
```bash
date +tt-%Y%m%d-%H%M
```

### Step 1.3: Check for Resume

**If `add_rounds` was set** (e.g., `/arc-think-tank +2`):
- Check if any `.task-tt-*.md` files exist
- If one found: read it, confirm its goal with the user: "Adding {N} more rounds to: {goal}. Proceeding..."
- If multiple found: list them with their goals and ask which to extend
- If none found: say "No existing session found. Provide a goal to start a new session." and **STOP**
- Parse `**Rounds Completed**:` from the task file (this is the reliable count of finished ideation rounds)
- If not present, fall back to `**Current Round**:` (for older sessions: treat "Final" as the total_rounds from that session, "0" as 0)
- Set `start_round = rounds_completed + 1`
- Set `total_rounds = start_round + add_rounds - 1`
- **Parse personality log from the task file** to restore previous personalities for no-repeat enforcement:
  - Check if the `## Personality Log` section exists in the task file
  - If it exists and has round entries:
    - Use bash to find the last `Round N:` line: `grep "^Round " .task-tt-{id}.md | tail -1`
    - Parse the line format: `Round N: Thinker={personality}, Vetter={personality}, Riffer={personality}`
    - Extract the three personality values and set the tracking variables:
      - `prev_thinker_personality` = extracted thinker value
      - `prev_vetter_personality` = extracted vetter value
      - `prev_riffer_personality` = extracted riffer value
  - If the Personality Log section doesn't exist (older session created before this feature):
    - Initialize all tracking variables as empty: `prev_thinker_personality = ""`, `prev_vetter_personality = ""`, `prev_riffer_personality = ""`
    - This ensures backward compatibility — first new round will select freely from all 4 personalities
    - Add the `## Personality Log` section header via Edit tool so logging works for the new rounds
  - If the section exists but has no round entries (shouldn't happen, but defensive):
    - Initialize all tracking variables as empty
- Skip to Phase 2 (do NOT re-create context files or re-run initialization)

**Only if no goal text was parsed and no add_rounds** (bare `/arc-think-tank` invocation):
- Check if any `.task-tt-*.md` files exist
- If one found: read it, show its goal, and ask "Resume this session, or start a new one?"
- If multiple found: list them with their goals and ask which to resume (or start new)
- **If resume**: Parse current round/step from the task file and jump to appropriate step
- **If start fresh or new**: Proceed to Step 1.4

**If goal text was parsed**: Skip resume check entirely — this is a new session.

### Step 1.4: Verify Materials

If material file paths were provided:
- Verify each file exists using Read tool
- If any file is missing, report which ones and ask user to confirm or provide corrections
- **WAIT for user if files are missing**

### Step 1.5: Create Context Files

**Create `.task-{id}.md`**:

```markdown
# Think Tank Session: {id}

## Goal
{The parsed goal text}

## Materials
{List of material file paths, or "None provided"}

## Session Progress
**Current Round**: 0
**Current Step**: Initialized
**Rounds Completed**: 0
**Started**: {timestamp}
**Last Updated**: {timestamp}

## File References
- Task context: .task-{id}.md
- Ideas file: .think-tank-{id}-ideas.md
- Report: .think-tank-{id}-report.md (created by judge)

## Personality Log

```

**Create `.think-tank-{id}-ideas.md`**:

```markdown
# Think Tank Ideas

**Goal**: {The parsed goal text}

**Format Guide**: Each idea has a sequential ID (A1, A2, ...), source attribution, description, a `Rounds Vetted` counter, and comments section. Vetters increment `Rounds Vetted` each pass and use (+N) to signal agreement with existing comments. The judge normalizes consensus scores by dividing raw (+N) by rounds vetted, so later ideas aren't penalized for having fewer vetting opportunities.

---

```

### Step 1.6: Report Initialization

Display to user:
```
Think Tank activated for: {goal}

Materials: {list of files or "none"}
Session ID: {id}

Starting Round {start_round} of {total_rounds}...
```

**DO NOT pause for confirmation** — proceed immediately to Phase 2.

---

## PHASE 2: Ideation Rounds (×N)

Run rounds from `start_round` through `total_rounds`. Each round consists of: Thinker → Vetter → Riffer.

- For new sessions: `start_round = 1`, `total_rounds = round_count` (default 5)
- For add-rounds sessions: `start_round` and `total_rounds` were set in Step 1.3

### Personality Initialization

Before the round loop starts, initialize 3 tracking variables for previous personalities:
- `prev_thinker_personality` = "" (empty)
- `prev_vetter_personality` = "" (empty)
- `prev_riffer_personality` = "" (empty)

For add-rounds sessions, these may already be populated from the resume parsing in Step 1.3. For new sessions, they start empty (meaning Round 1 selects freely from all 4 personalities with no exclusion).

### Round-Specific Thinker Guidance

Select guidance based on each round's **position within its run** (not absolute round number). For a run of N rounds, map each round to a phase:

| Position | Condition | Guidance |
|----------|-----------|----------|
| **First round** | round == start_round | "Cast a wide net. Explore diverse angles, unconventional approaches, different scales of ambition. Prioritize breadth and originality." |
| **Early rounds** | first quarter of remaining rounds | "Build on what's working. Look at vetter feedback from earlier rounds. Generate ideas that address gaps or weaknesses. Explore adjacent territory." |
| **Middle rounds** | middle of run | "Go deeper. Push boundaries on the most promising directions. Try combining elements from different ideas in novel ways. Challenge assumptions." |
| **Late rounds** | third quarter of remaining rounds | "Refine and specialize. Focus on high-impact, feasible directions. Generate more detailed, implementation-ready ideas. Fill remaining gaps." |
| **Final round** | round == total_rounds | "Best final thinking. This is the last round. Make each idea count. Synthesize everything learned from previous rounds and feedback." |

For short runs (1-2 rounds), compress: Round 1 gets "wide net" guidance, final round gets "best final thinking." For a single round, use "Cast a wide net but make each idea count — this is both the first and last round."

### For each round (start_round through total_rounds):

**A. Update task context**:
- Edit `.task-{id}.md` to update Current Round and Current Step
- Current Step: "Thinker"

**B. Select personalities for this round**:

Use the Bash tool 3 times to randomly select a personality for each role. The 4 available personalities are: `contrarian`, `pragmatist`, `visionary`, `connector`.

**If the previous personality tracking variable is empty** (Round 1 of a new session, or first round after resume with no personality log):
```bash
echo "contrarian pragmatist visionary connector" | tr ' ' '\n' | shuf -n 1
```

**If the previous personality tracking variable is set** (Round 2+, or first round after resume with personality log):
```bash
echo "contrarian pragmatist visionary connector" | tr ' ' '\n' | grep -v "{prev_thinker_personality}" | shuf -n 1
```

Run the appropriate command for each role:
1. Select thinker personality (exclude `prev_thinker_personality` if set)
2. Select vetter personality (exclude `prev_vetter_personality` if set)
3. Select riffer personality (exclude `prev_riffer_personality` if set)

Store the results as `thinker_personality`, `vetter_personality`, and `riffer_personality` for use in agent prompts and logging.

**C. Launch Thinker** (Opus, ultrathink):
- Use Task tool with `subagent_type: "ca-think-tank-thinker"`
- Prompt: `"ultrathink\n\nYou are the Thinker in Round {R} of {total_rounds} of a creative think tank.\n\nYour personality this round is {Thinker_Personality}. Read agents/personalities/{thinker_personality}.md and adopt its reasoning style, evaluation criteria, and approach. Your outputs should reflect this personality substantively — not just in tone but in what you prioritize, what you challenge, and how you evaluate ideas.\n\nYour personality name for output attribution: {Thinker_Personality}\n\nTask context file: .task-{id}.md\nIdeas file: .think-tank-{id}-ideas.md\n\nRound guidance: {round-specific guidance from table above}\n\nRead the task context and materials, read all existing ideas and comments, then generate 5 new ideas. Append them to the ideas file with sequential IDs starting after the highest existing ID."`
- Note: The personality is ADDITIVE with the round-specific guidance. Guidance says "what to focus on this round" (e.g., cast a wide net, refine and specialize). Personality says "how to think about it" (e.g., challenge assumptions, focus on feasibility). Both are included in the prompt.
- Wait for completion

**D. Display progress**:
```
Round {R}/{total_rounds} — Thinker/{Thinker_Personality} complete (5 new ideas added). Vetting...
```

**E. Update task context**: Current Step: "Vetter"

**F. Launch Vetter** (Sonnet):
- Use Task tool with `subagent_type: "ca-think-tank-vetter"`
- Prompt: `"You are the Vetter in Round {R} of {total_rounds} of a creative think tank.\n\nYour personality this round is {Vetter_Personality}. Read agents/personalities/{vetter_personality}.md and adopt its reasoning style, evaluation criteria, and approach. Your outputs should reflect this personality substantively — not just in tone but in what you prioritize, what you challenge, and how you evaluate ideas.\n\nYour personality name for output attribution: {Vetter_Personality}\n\nTask context file: .task-{id}.md\nIdeas file: .think-tank-{id}-ideas.md\n\nRead all ideas and evaluate each one. Add new comments or increment (+N) on existing comments you agree with. Focus on feasibility, impact, originality, and risks."`
- Wait for completion

**G. Display progress**:
```
Round {R}/{total_rounds} — Vetter/{Vetter_Personality} complete. Riffing on most promising idea...
```

**H. Update task context**: Current Step: "Riffer"

**I. Launch Riffer** (Opus):
- Use Task tool with `subagent_type: "ca-think-tank-riffer"`
- Prompt: `"You are the Riffer in Round {R} of {total_rounds} of a creative think tank.\n\nYour personality this round is {Riffer_Personality}. Read agents/personalities/{riffer_personality}.md and adopt its reasoning style, evaluation criteria, and approach. Your outputs should reflect this personality substantively — not just in tone but in what you prioritize, what you challenge, and how you evaluate ideas.\n\nYour personality name for output attribution: {Riffer_Personality}\n\nTask context file: .task-{id}.md\nIdeas file: .think-tank-{id}-ideas.md\n\nRead all ideas and vetter feedback. Pick the idea with the most improvement potential and create ONE evolved riff. Append it to the ideas file with the next sequential ID."`
- Wait for completion

**J. Display progress**:
```
Round {R}/{total_rounds} complete ✓ ({total ideas} ideas so far)
```

**K. Log personality selections**:
- Use the Edit tool to append to the `## Personality Log` section of `.task-{id}.md`:
  ```
  Round {R}: Thinker={thinker_personality}, Vetter={vetter_personality}, Riffer={riffer_personality}
  ```

**L. Update personality tracking variables** for next round:
- `prev_thinker_personality` = `thinker_personality`
- `prev_vetter_personality` = `vetter_personality`
- `prev_riffer_personality` = `riffer_personality`

**M. If round < total_rounds**, display:
```
Starting Round {R+1}...
```

---

## PHASE 3: Final Vetting

After all rounds are complete:

### Step 3.1: Update task context
- Current Round: "Final"
- Current Step: "Final Vetter"

### Step 3.2: Select personality for final vetter

Use the Bash tool to randomly select a personality for the final vetter, excluding the last round's vetter personality (stored in `prev_vetter_personality`):

```bash
echo "contrarian pragmatist visionary connector" | tr ' ' '\n' | grep -v "{prev_vetter_personality}" | shuf -n 1
```

Store the result as `final_vetter_personality` for use in the agent prompt and logging.

### Step 3.3: Display progress
```
All {total_rounds} rounds complete. Running final vetting pass...
```

### Step 3.4: Launch Final Vetter (Sonnet)
- Use Task tool with `subagent_type: "ca-think-tank-vetter"`
- Prompt: `"You are the Vetter doing the FINAL evaluation pass of a creative think tank.\n\nYour personality for this final pass is {Final_Vetter_Personality}. Read agents/personalities/{final_vetter_personality}.md and adopt its reasoning style, evaluation criteria, and approach. Your outputs should reflect this personality substantively — not just in tone but in what you prioritize, what you challenge, and how you evaluate ideas.\n\nYour personality name for output attribution: {Final_Vetter_Personality}\n\nTask context file: .task-{id}.md\nIdeas file: .think-tank-{id}-ideas.md\n\nThis is the final vetting round after {total_rounds} rounds of ideation. All ideas are now in the file. Evaluate every idea with fresh eyes. Add new comments where you have insights, and increment (+N) on comments you agree with. Your feedback will directly inform the judge's final ranking."`
- Wait for completion

### Step 3.5: Log final vetter personality
- Use the Edit tool to append to the `## Personality Log` section of `.task-{id}.md`:
  ```
  Final Vetter: {final_vetter_personality}
  ```

### Step 3.6: Display progress
```
Final vetting complete. Judging...
```

---

## PHASE 4: Judgment

### Step 4.1: Update task context
- Current Step: "Judge"

### Step 4.2: Launch Judge (Opus)
- Use Task tool with `subagent_type: "ca-think-tank-judge"`
- Prompt: `"You are the Judge of a creative think tank that has completed {total_rounds} rounds of ideation.\n\nTask context file: .task-{id}.md\nIdeas file: .think-tank-{id}-ideas.md\nReport file to write: .think-tank-{id}-report.md\n\nRead all ideas with their comments and consensus signals. Build redundancy clusters, select the strongest representative from each, rank the top 5, and write the final report."`
- Wait for completion

---

## PHASE 5: Present Results

### Step 5.1: Read and display the report
- Read `.think-tank-{id}-report.md`
- Display the full report to the user

### Step 5.2: Show file references
```
---

Session files:
- Ideas: .think-tank-{id}-ideas.md ({N} ideas generated)
- Report: .think-tank-{id}-report.md
- Context: .task-{id}.md
```

### Step 5.3: Update task context
- Current Step: "Complete"
- Rounds Completed: {total_rounds}
- Last Updated: {timestamp}

### Step 5.4: Offer follow-up options
```
What would you like to do?

1. Dive deeper into the #1 ranked idea
2. Explore a different idea from the report
3. Run another think tank session with a refined goal
4. Start implementing the top idea
5. Something else
```

---

## Error Handling

- **If an agent fails**: Report which agent failed (Thinker/Vetter/Riffer/Judge), which round, and ask user:
  - "Retry this step?"
  - "Skip and continue?" (skipping a vetter or riffer is safe; skipping a thinker means fewer ideas)
  - "Abort the session?"
- **If ideas file gets corrupted**: The task context file tracks progress; worst case, re-read the ideas file to determine current state
- **If user interrupts**: Task context file has enough state to resume later

## Implementation Notes

### Serial Execution

All agent calls are serial — each builds on the previous step's output. No TeamCreate needed. This avoids concurrency issues with the shared ideas file.

### Token Cost Profile (for N rounds)

- **N Thinker calls** (Opus, ultrathink) — heaviest cost
- **N+1 Vetter calls** (Sonnet) — moderate cost (N rounds + 1 final)
- **N Riffer calls** (Opus) — moderate cost
- **1 Judge call** (Opus) — moderate cost
- Total: 3N+2 agent calls. Default (5 rounds) = 17 calls.

### Model Routing

| Agent | Model | Why |
|-------|-------|-----|
| Thinker | Opus | Creative generation benefits from strongest model + ultrathink |
| Vetter | Sonnet | Evaluation is analytical, not creative — Sonnet is sufficient and cost-efficient |
| Riffer | Opus | Evolution/combination requires creative synthesis |
| Judge | Opus | Final ranking needs nuanced judgment across many dimensions |

### Ultrathink Usage

- **ca-think-tank-thinker**: YES — invoked with ultrathink for deep creative analysis
- **ca-think-tank-vetter**: NO — analytical evaluation, standard thinking is sufficient
- **ca-think-tank-riffer**: NO — creative but focused on one idea, standard thinking is sufficient
- **ca-think-tank-judge**: NO — ranking and synthesis, standard thinking is sufficient

---

## Example User Experiences

### Default (5 rounds)
```
User: /arc-think-tank How can we reduce customer churn for our SaaS product?
Claude: Think Tank activated for: How can we reduce customer churn for our SaaS product?
       Session ID: tt-20250213-1430 | Rounds: 5
       Starting Round 1 of 5...
       [... 5 rounds of Thinker → Vetter → Riffer ...]
       All 5 rounds complete. Running final vetting pass...
       [Report with top 5 ranked ideas]
```

### Custom rounds
```
User: /arc-think-tank How can we reduce churn? [3 rounds]
Claude: Think Tank activated for: How can we reduce churn?
       Session ID: tt-20250213-1430 | Rounds: 3
       Starting Round 1 of 3...
       [... 3 rounds ...]
       [Report]
```

### Add rounds to existing session
```
User: /arc-think-tank +2
Claude: Adding 2 more rounds to: How can we reduce customer churn for our SaaS product?
       Starting Round 6 of 7...
       [... 2 more rounds, picking up where the session left off ...]
       [New report re-judging ALL ideas including the new ones]
```
