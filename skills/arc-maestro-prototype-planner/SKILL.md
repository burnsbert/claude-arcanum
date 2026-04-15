---
name: arc-maestro-prototype-planner
description: "Generate a prototype story from a product document (Notion export, PDF, markdown). Takes a product idea or spec and produces an actionable prototype story through interactive scope discovery. Use when someone says 'create a prototype story', 'plan a prototype', or 'turn this into a prototype'."
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion, WebSearch, WebFetch
argument-hint: "[--assume=technical|non-technical] <filepath>"
user-invocable: true
---

# Maestro Prototype Planner

Transform a product document into a buildable prototype story. Creates a
standalone project directory containing the story file and source materials in
`docs/`, ready for a developer (or `/arc-maestro`) to implement as a
self-contained interactive prototype.

## Arguments

**Input**: `$ARGUMENTS` (path to a product document -- markdown, PDF, or text)

## Step 1: Document Intake

1. **Record the launch directory as `LAUNCH_DIR`** (absolute path) -- run
   `pwd` once and store the result. All references to the scratch file
   (`.maestro-prototype-scratch.md`) in later steps use `$LAUNCH_DIR`, NOT
   the working directory, because Step 4 changes into the prototype project.

2. **Remove stale working files**:
   - Delete `$LAUNCH_DIR/.maestro-prototype-scratch.md` if present (leftover from a prior run)

3. **Parse arguments**:
   - **Check for `--assume` flag**: When `$ARGUMENTS` begins with
     `--assume=technical` or `--assume=non-technical`, extract and remove the
     flag. The remainder is the file path.
     - `--assume=technical` -> set `TECHNICAL_AUDIENCE` = true
     - `--assume=non-technical` -> set `TECHNICAL_AUDIENCE` = false
     - No flag -> set `TECHNICAL_AUDIENCE` = false (default is non-technical)
   - **Validate the remaining input**:
     - If empty or missing, say:
       - "A file path to a product document is required (Notion export,
         markdown, PDF, etc.)."
       - "Example: `/arc-maestro-prototype-planner ./receipt-image-feature.md`"
       - **STOP**
   - Expand the path (resolve `~`, `./`), then Read the file.
   - If the file cannot be read, report the error and **STOP**.

4. **Extract key elements** (adapt to whatever structure the document uses):
   - Product or feature name
   - Problem statement -- what user pain does this address?
   - Target users -- who benefits?
   - Proposed solution -- what is the idea?
   - Success metrics -- how is success measured?
   - Risks and open questions
   - Existing app context -- does this belong to an existing product?
   - Mockups, screenshots, or image references
   - Not every document will contain all of these. Extract what is available.
   - **Disregard time estimates** in the document. They are unreliable and
     should not be repeated, validated, or factored into scope. Exception: if
     the overall effort appears to span multiple weeks, flag that as a
     concern for Step 3.

5. **Record private observations** (do NOT share with the user yet):
   - Product documents often come from non-technical authors. Part of this
     workflow's value is providing a technical sanity check. As you parse,
     note anything that warrants attention:
     - **Infeasible requests** -- asks for something that doesn't exist or
       would require disproportionate effort for a prototype
     - **Technical misunderstandings** -- incorrect assumptions about how a
       technology works
     - **Self-defeating proposals** -- an approach that would undermine the
       stated goal
     - **Critical gaps** -- the concept depends on something left unspecified
     - **Scope mismatch** -- what is described is a full product, not a
       prototype
   - Save these observations to your scratch file. They become actionable
     questions with options in Step 3.

## Step 2: Comprehension Check

1. Present a 5--8 sentence summary of your understanding of the document.
   Cover only understanding -- no concerns, feasibility notes, or technical
   flags here. Those are reserved for Step 3 where they become questions
   with options.
2. Ask: "Does this capture the intent correctly, or should I adjust anything?"
3. **WAIT for confirmation.** If the user corrects your understanding, revise
   and re-confirm before proceeding.

## Step 3: Scope Conversation

This is a **dialogue, not a questionnaire**. Ask one question at a time,
adapt based on answers, and follow up when something is ambiguous.

### Audience Handling

**When `TECHNICAL_AUDIENCE` is false** (the default): the person answering is
typically a non-technical product owner. Adjust accordingly:

- Explain technical concepts through analogies rather than jargon.
- Lead each question with your recommended answer and the reasoning behind
  it, then list alternatives. Product owners want guidance, not a quiz.
- Express trade-offs concretely: "This means building two additional screens
  and handling the case where the service is unavailable" -- not "This adds
  complexity."
- When a technical term is unavoidable, follow it immediately with a
  plain-language explanation in parentheses.
- Be opinionated. Your technical judgment is the value here. A strong
  recommendation with clear reasoning beats a balanced but unhelpful list.

**When `TECHNICAL_AUDIENCE` is true**: skip analogies and plain-English
expansions. Be direct and concise. Assume familiarity with technical
concepts.

### Mechanics

1. **Draft a question plan** based on what you learned from the document.
   Write it to `$LAUNCH_DIR/.maestro-prototype-scratch.md` (absolute
   path -- Step 4 changes CWD into the prototype project, so always use
   `$LAUNCH_DIR`). This is your private scratchpad -- revise it as the
   conversation progresses.

2. **Ask ONE question at a time** using AskUserQuestion. Wait for the
   response before choosing the next question.

3. **Follow up when needed.** If an answer is vague, surprising, or carries
   implicit context, clarify before moving on. A brief "Just to confirm --
   do you mean X or Y?" is always worthwhile.

4. **Update the plan** after each answer. Drop questions already answered.
   Add new ones when topics surface.

5. **Surface concerns as questions with options.** Recommend the option you
   consider best with `(Recommended)`. Label clearly unwise options with
   `(Not recommended)` and explain why.

6. **Stop when you have enough.** When you can write a clear, buildable
   story, summarize what you have and confirm readiness:

   > "Ready to set up the project directory and write the story. This will
   > create a new directory and files. Proceed?"

   **WAIT for explicit go-ahead.** Do NOT move to Step 4 until the user
   approves.

### Topics to Address

Use your judgment about which topics matter for the current document. Not
every category applies to every prototype:

- **Product context** -- new product or feature for an existing one? If
  existing, which product and where is the repo?
- **Prototype objective** -- demonstrate a workflow, prove technical
  feasibility, or both?
- **Target audience** -- who sees this and what feedback is sought?
- **Key interactions** -- which user flows must the prototype demonstrate?
- **Real vs. simulated** -- for each interaction, should data and integrations
  be live or mocked?
- **Visual fidelity** -- match the existing app, approximate the style, or
  wireframe-level?
- **Conditional topics** -- technical proof specifics (if relevant), user
  testing goals (if relevant), API or integration decisions (if relevant)

### Research When Uncertain

If the conversation surfaces technologies, APIs, or approaches you are not
confident about, use `WebSearch` / `WebFetch` to verify before committing
them to the story. If research reveals something that changes the picture --
a library that does not exist, an API with unexpected limitations, a simpler
alternative -- bring it back to the user and ask how to adjust.

## Step 4: Project Scaffolding

1. **Choose a base directory** (check in order, first match wins):
   1. CWD is `$HOME` or `$HOME/src` -> base = CWD
   2. Inside a git repo -> base = parent of the repo root
      (`git rev-parse --show-toplevel`, then go up one level). Prototypes
      are standalone -- they do not belong inside another codebase.
   3. Otherwise -> base = CWD

2. **Determine the directory name**: `prototype-{kebab-case-name}`.
   If `{base}/prototype-{kebab-case-name}/` already exists, append a
   numeric suffix (`-2`, `-3`, ...) until unique.

3. **Create the directory structure**:
   ```bash
   mkdir -p {base}/prototype-{kebab-case-name}/docs
   ```

4. **Locate the reference product repo** (when applicable):
   - If the prototype targets an existing product, the repo should be
     available locally for the implementer to study UI patterns.
   - If the user provided a repo path or URL during Step 3, verify it
     exists.
   - If not found locally, ask the user where to find it and offer to
     clone -- **wait for confirmation** before running `git clone`.
   - Record the path for the story file.

5. **Select a tech stack**:
   - Choose the simplest stack that satisfies the prototype requirements.
     Priorities: fast to build, runs locally without deployment, can look
     like a real application.
   - **Default recommendation**: Next.js or Vite + React with Tailwind CSS
   - **For heavy data or form interactions**: add a JSON file or SQLite for
     persistence
   - **For technical proofs requiring specific tools**: use whatever is
     needed (e.g., Python + OpenCV for image processing)
   - **For very simple interactions**: plain HTML/CSS/JS may be enough
   - Present the recommendation and confirm with the user.

6. **Confirm the setup**:
   - Display: directory path, tech stack, reference repo (if any),
     real-vs-simulated summary
   - Ask: "Does this look right?"
   - **WAIT for confirmation.** Revise and re-confirm if the user requests
     changes.

## Step 5: Story Generation

1. **Story ID**: Always `PRT-1` (each prototype has its own directory, so
   there is only ever one story).

2. **Copy source materials into `docs/`**:
   - Copy the original input document to `{prototype-dir}/docs/`
   - Copy any referenced files (images, screenshots, PDFs, spreadsheets)
     to `{prototype-dir}/docs/`
   - If a referenced file cannot be located, note it under Open Questions
     in the story.

3. **Write the story file** at `{prototype-dir}/docs/PRT-1.md`:

```markdown
# PRT-1: {Feature Name} -- Interactive Prototype

## Source Material
- **Original document**: {path to source document}
- **Local copy**: {filename in docs/}
- **Supporting files**: {list of other files in docs/, or "None"}
- **Product**: {product name}
- **Author**: {if known}
- **Date**: {current date}
- **Generated by**: arc-maestro-prototype-planner

## Overview

### Purpose
{2-3 sentences: what the prototype demonstrates and why it matters}

### Intended Audience
{Who will evaluate this and what feedback is sought}

### Success Criteria
{What constitutes a successful prototype -- derived from the scope conversation}

## Interactions

{For each interaction identified in Step 3, create a section:}

### Interaction 1: {Name}
**User Action**: {What the user does}
**Expected Response**: {What the prototype shows or does}
**Data Approach**: {Real / Simulated / Placeholder}
**Acceptance Criteria**:
- {Testable criterion}
- {Testable criterion}

### Interaction 2: {Name}
...

## Technical Approach

### Stack
- **Framework**: {chosen framework}
- **Styling**: {CSS approach}
- **Data Handling**: {mock files, API calls, etc.}
- **Additional Tools**: {any extra libraries}

### Real vs. Simulated

| Component | Approach | Notes |
|-----------|----------|-------|
| {component} | {Real/Simulated/Placeholder} | {details} |

### Technical Proof Points
{If applicable -- capabilities being demonstrated}

## Visual Reference

### Target Product
- **Product**: {name, or "New product"}
- **Repo**: {local path, or "N/A"}
- **Key UI files**: {paths to study for styling, or "N/A"}

### Styling Guidance
- {Color scheme, layout patterns, component conventions}
- {Specific UI elements to replicate}

## Project Setup

### Directory
`{prototype directory path}`

### Running Locally
```bash
cd {prototype directory path}
{install command}
{run command}
```

### Prerequisites
- {Runtime versions}
- {API keys or setup needed}

## Scope

### Included
{Bulleted list of what IS in scope}

### Excluded
{Bulleted list of what is explicitly NOT in scope}

### Deliberate Simplifications
{Things intentionally faked or reduced for the prototype}

## Open Questions
{Unresolved items from the document or scope conversation}

## Reference

### Document Summary
{Brief summary of the source document}

### Key Requirements from Source
{Specific requirements extracted from the document}
```

4. **Review with user**:
   - Show the generated file path and list of docs copied
   - Display the full story content
   - Say: "You can request changes if anything needs adjustment."
   - Ask: "Do you approve this story?"
   - Apply edits if requested, then re-ask.

5. **After approval**:
   - Delete `$LAUNCH_DIR/.maestro-prototype-scratch.md` (it is a working
     file, not an artifact)
   - Print next-step guidance:

```
Prototype story ready: {prototype-dir}/docs/PRT-1.md

Next steps:
  1. Review the story and make any final edits
  2. cd {prototype-dir}
  3. Start a new Claude Code session
  4. /arc-maestro docs/PRT-1.md

Maestro will scaffold the project and implement each interaction from the story.
```

## Important Notes

- This skill ONLY creates the story. It does NOT build the prototype.
  Implementation is for `/arc-maestro` or a developer.
- The story should be detailed enough that someone can build from it without
  the original source document.
- Maintain tight scope. A prototype that attempts too much is less useful than
  one that does fewer things well.
- **Disregard time estimates** -- do not generate, repeat, or validate them.
  Exception: flag overall scope that appears to require multiple weeks so
  the user can trim.
- Always favor the simplest approach that demonstrates the key interactions.
- The prototype is throwaway code. Optimize for speed of creation and clarity
  of demonstration, not for code quality or long-term maintainability.
- **Scratch file cleanup**: delete `$LAUNCH_DIR/.maestro-prototype-scratch.md`
  after approval. Use `$LAUNCH_DIR`, never the current CWD -- Step 4 changes
  directories. It is a working file, not a deliverable.
