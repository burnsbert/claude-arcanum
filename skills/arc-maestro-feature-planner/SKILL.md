---
name: arc-maestro-feature-planner
description: "Generate one or more production stories from product docs or a description. Conducts an interactive interview to scope a feature, then writes story files plus feature/PRD/technical-design docs into a target repo's .stories/ directory (cloning or creating the repo if needed). Use when someone says 'create a feature plan', 'plan a feature', 'break this into stories', or 'turn this into a backlog'."
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion, WebSearch, WebFetch
argument-hint: "<description | filepath | filepath filepath ... | directory>"
user-invocable: true
---

# Maestro Feature Planner

Convert one or more product documents (or an inline description) into a
**production-ready story backlog** for a real feature. Generates:

- `.stories/feature-<slug>.md` -- overview with story checklist
- `.stories/feature-<slug>-prd.md` -- product requirements for the dev team
- `.stories/feature-<slug>-technical-design.md` -- technical design document
- `.stories/<PREFIX>-NNNN.md` -- one file per story (e.g., `BIL-1001.md`)

All artifacts land in the target repo's `.stories/` directory. For existing
products, the skill works with a local clone (cloning first if needed). For
entirely new products, it initializes a fresh repo.

**This is NOT a prototype.** The output is real stories intended to ship.
There is no throwaway code.

## Arguments

**Input**: `$ARGUMENTS`

Accepted forms:
- **Empty** -> print usage and stop.
- **A single existing directory** -> read every `.md` / `.txt` file in it
  (non-recursive, sorted).
- **One or more existing file paths** (space-separated, `~` / `./` resolved)
  -> read each in order.
- **Anything else** -> treat the entire `$ARGUMENTS` string as an inline
  feature description.

## Step 1: Input Resolution

1. **Record the launch directory as `LAUNCH_DIR`** (absolute path) -- run
   `pwd` once and store the result. All references to the scratch file
   (`.maestro-feature-scratch.md`) in later steps use `$LAUNCH_DIR`, NOT
   the working directory, because Step 4 changes into the target repo.

2. **Clean up prior scratch file**: delete
   `$LAUNCH_DIR/.maestro-feature-scratch.md` if it exists.

3. **Validate `$ARGUMENTS`**:
   - If empty or missing, display:
     - "This skill needs a feature description, a file path, multiple file
       paths, or a directory of source documents."
     - "Examples:"
     - "  `/arc-maestro-feature-planner ./product-spec.md`"
     - "  `/arc-maestro-feature-planner ./spec.md ./design-doc.md`"
     - "  `/arc-maestro-feature-planner ./docs/feature-x/`"
     - "  `/arc-maestro-feature-planner Add two-factor auth for the portal`"
     - **STOP**

4. **Classify the argument** (check in order, first match wins):

   **4a. Try the raw unsplit `$ARGUMENTS` as a single path** (handles spaces
   in paths). After `~`/`./` expansion, check whether the entire string
   resolves. Use a concrete command: `test -e "$expanded" && echo yes`.
   If it resolves:
   - `test -d "$expanded"` -> `source_type = "dir"`, `sources = [that path]`
   - Otherwise -> `source_type = "files"`, `sources = [that path]`
   - Done. Skip the rest of step 4.

   **4b. Otherwise split `$ARGUMENTS` on whitespace** -> `tokens`. Classify
   each token after `~`/`./` expansion:
   - A token is **path-like** if it contains `/`, starts with `./` or `~`,
     or ends with `.md` / `.txt`.
   - For each token, run `test -e "$expanded"` and record whether it exists.

   **4c. Determine `source_type`**:
   - If **every** token exists -> `source_type = "files"`,
     `sources = tokens`.
   - If **any** token is path-like but missing -> **STOP**. Report each
     unresolvable path-like token and ask the user to correct it. Do not
     silently fall through to inline.
   - If **no** token is path-like -> `source_type = "inline"`,
     `sources = [full $ARGUMENTS string]`.

5. **Load the sources**:
   - `dir`: list `*.md` and `*.txt` files (non-recursive, sorted), Read
     each. Subdirectories are intentionally skipped; tell the user if any
     exist and ask whether to flatten first.
   - `files`: Read each path in order.
   - `inline`: the entire `$ARGUMENTS` string is the source content.

6. **Assemble a working buffer**: concatenate all source content with
   `=== <filename> ===` separators. Remember the absolute paths -- they
   will be copied into `.stories/docs/` in Step 5.

7. **If any file read fails**: report the failure and **STOP**.

## Step 2: Orientation

### 2.1 Audience question (ALWAYS first)

Use AskUserQuestion:

> "Should I address you as a technical or non-technical audience?"

Options:
- **Technical** (Recommended for developers) -- direct language, no
  analogies, assumes familiarity with code and infrastructure.
- **Non-technical** -- plain-English explanations, strong defaults,
  concrete trade-offs, minimal jargon.

Store the answer as `TECHNICAL_AUDIENCE` (true / false).

### 2.2 Parse the source material

Extract whatever is available (not every source will contain everything):

- Product or feature name
- Problem statement -- what user pain does this address?
- Target users or personas
- Proposed solution -- the core idea
- Success metrics
- Risks and open questions
- Existing app context -- which product does this belong to?
- References (mockups, screenshots, linked tickets, URLs)

**Disregard time estimates** in the source docs. Exception: if the scope
appears to span multiple quarters, record that as a concern for Step 3.

### 2.3 Record concerns privately (do NOT present yet)

Note any of the following in your scratch file:
- **Infeasible or impractical** requests
- **Technical misunderstandings** -- incorrect assumptions about how a
  technology works
- **Self-defeating proposals** -- approaches that would undermine the
  stated goal
- **Critical gaps** -- the design depends on something unspecified
- **Scope concerns** -- not "too large in general" but "this looks like it
  spans many sprints or quarters" -- flag so the user can trim

These will become actionable questions with options in Step 3.

### 2.4 Summarize understanding

Present a 5--8 sentence summary of what you understood. **No concerns yet.**
Ask: "Is this understanding correct, or should I adjust anything?"

**WAIT for confirmation.** If the user corrects you, revise and re-confirm
before proceeding.

## Step 3: Discovery Interview

This is a **conversation, not a checklist**. One question at a time,
adapting on the fly.

### Audience handling

- `TECHNICAL_AUDIENCE = true` -> be direct and concise. Assume the user
  understands APIs, migrations, feature flags, and framework conventions.
- `TECHNICAL_AUDIENCE = false` -> explain technical concepts through
  analogies. Always present a recommended default first. Show concrete
  trade-offs ("this adds roughly two extra screens and requires handling
  downtime scenarios") rather than abstract ones. Avoid jargon without an
  immediate plain-language explanation in parentheses.

### Mechanics

1. **Draft a question plan.** Write it to
   `$LAUNCH_DIR/.maestro-feature-scratch.md` (absolute path -- Step 4
   changes CWD into the target repo, so always use `$LAUNCH_DIR`). This is
   your private scratchpad; revise it as the conversation progresses.

2. **Ask ONE question at a time** using AskUserQuestion. Wait for each
   response before deciding what to ask next.

3. **Clarify ambiguity.** If a response is vague, surprising, or carries
   implicit context you do not share, follow up before proceeding. A brief
   "Just to confirm -- do you mean X or Y?" is always worthwhile.

4. **Revise the plan** after each answer. Remove questions already answered.
   Add new ones when topics surface.

5. **Frame concerns as questions with options.** Recommend the path you
   consider best with `(Recommended)`. Label unwise options with
   `(Not recommended)` and explain why.

6. **There is no fixed question count.** Keep asking until you have enough
   clarity to produce a solid backlog. Intelligently determine which topics
   apply -- a pure backend API change does not need design-readiness
   questions; an AI feature needs prompt-injection considerations that a
   CRUD form does not. **When uncertain, ask.** A question that proves
   unnecessary costs seconds; an assumption that proves wrong costs an
   entire story rewrite.

7. **Know when to wrap up.** When you have sufficient material, present a
   summary to the user: the feature slug and story-ID prefix, the target
   repo (and whether you will clone it), the candidate story list with
   titles, and the feature-branch decision. Then ask:

   > "Do you have any questions for me before I proceed?"

   **WAIT for the response.** If the user asks questions, answer them
   thoroughly -- these follow-ups often surface important details that
   improve the backlog. Continue until the user is satisfied. Then say:

   > "Ready to set up the target directory and generate the backlog. This
   > will create or enter a repo directory and write files. Proceed?"

   **WAIT for explicit confirmation.** Do NOT advance to Step 4 until the
   user approves -- in auto mode, Step 4 would otherwise silently mutate
   the filesystem (mkdir, git init, git clone, file writes).

### Topics to Cover

Not every topic applies to every feature. Use your judgment -- choose the
ones that matter and skip the rest:

- **Product context** -- is this a feature for an existing product or
  something entirely new? If existing, which product?
- **Target repo(s)** -- if existing: which repo(s)? If new: what should the
  repo be named? Where should it live (default: `~/src/<name>`)? If
  multiple repos: deployment order and backward-compatibility constraints.
- **Feature slug** -- a short kebab-case identifier (e.g.,
  `two-factor-auth`). Auto-suggest one from the sources and confirm. The
  slug drives filenames **and** the story-ID prefix (see Step 5.1). When
  you confirm the slug, also preview the derived prefix (e.g., "Slug
  `two-factor-auth` -> prefix `TFA`, so stories will be `TFA-1001`,
  `TFA-1002`, ...") so the user can object before the IDs are used
  throughout. If collision handling (Step 5.1, rule 5) mutates the prefix
  later, inform the user at that point.
- **Goals and success criteria** -- how do we know it is done?
- **Audience and stakeholders** -- who uses it, who reviews it, who approves?
- **Scope decomposition** -- propose 3--6 candidate stories based on the
  sources and suggest a dependency order. Let the user add, remove, split,
  or merge. Each story needs a one-line purpose.
- **External dependencies** -- does the feature require new third-party
  APIs, SDKs, or services? If so: auth model, sandbox availability, rate
  limits, cost, and vendor ownership. Surface any new env vars, API keys,
  or service accounts needed.
  **Version currency**: when introducing a new SDK, library, or framework,
  use `WebSearch` to verify the latest stable version -- do NOT rely on
  training data. Document reasoning if pinning an older version. Existing
  outdated dependencies are out of scope unless they interfere with the
  current feature.
- **Data migration** -- does the feature change the data model for existing
  records? Does anything need backfilling? This often becomes its own
  story with rollback considerations.
- **Design readiness** -- are finalized designs available (Figma, mockups,
  wireframes)? If so, get links. If not, what is the timeline and who owns
  it? It is also acceptable for the implementer to derive the UI from
  requirements -- just confirm that expectation so stories are written
  accordingly.
- **Technical approach** -- languages, frameworks, integration points.
  Reference patterns found in the codebase (use `Glob` / `Grep`). Cover
  new infrastructure needs (cloud resources, queues, databases, pipeline
  changes) and observability (dashboards, alerts, log instrumentation).
- **Customer impact** -- if modifying existing functionality: how might
  current users be affected? Feature flag for rollout? Backward
  compatibility during transition? Non-backward-compatible API changes
  and their migration path? These concerns often warrant explicit stories.
- **Performance and scalability** -- new queries on large tables, new async
  processing at scale, high-traffic endpoints, N+1 patterns. Surface
  these so they become acceptance criteria or dedicated stories.
- **Security** -- new auth flows, data exposure surfaces, permission model
  changes, multi-tenancy concerns. For AI features: prompt injection
  vectors, output sanitization, misuse guardrails.
- **Feature branch strategy** -- does the user want a shared feature branch
  (e.g., `<slug>-<month>-<year>`) that story branches merge into before
  landing in the main branch? Default: yes for multi-story features, no
  for single-story ones.
- **Risks and open questions** -- collect for the PRD and technical design.
  Phased rollout? Kill switch?

### Research loop

If the interview surfaces technologies, APIs, or approaches you are not
confident about, use `WebSearch` / `WebFetch` to verify. If research reveals
something that changes the picture -- a library that does not exist, an API
with an unexpected limitation, a simpler approach -- bring it back to the
user before incorporating it into the design. Do not rush to file
generation.

## Step 4: Repository Setup

### 4a. Existing product

1. Resolve a canonical repo name and URL from the interview answers.
2. Search for a local clone (check in order, use the first hit):
   - `~/src/<repo-name>` (as written)
   - `~/src/<repo-name-lowercased>`
   - Scan all `~/src/*/.git/config` for the remote URL:
     ```bash
     hit=$(grep -rl "<repo-url-fragment>" ~/src/*/.git/config 2>/dev/null | head -1)
     [ -n "$hit" ] && dirname "$(dirname "$hit")"
     ```
     `grep -rl` returns a path like `/Users/you/src/myrepo/.git/config`.
     The repo root is the **grandparent** (strip `/.git/config`), NOT the
     immediate parent (which is `.git/`). The `dirname $(dirname ...)` above
     produces `/Users/you/src/myrepo`. Use a URL fragment that matches both
     SSH and HTTPS remote styles (e.g., `org/repo`).
3. **If not found**: tell the user: "I could not find a local clone. I would
   like to run `git clone <url> ~/src/<repo-name>` -- okay?" **Wait for
   confirmation.**
4. `cd` into the repo. `mkdir -p .stories`. **Do not touch** any existing
   files in `.stories/` -- add new ones alongside them.
5. If the interview selected a feature branch strategy, record the branch
   name. **Do not create the branch.** The skill only suggests -- the user
   creates it. Mention the branch in `feature-<slug>.md` under "Feature
   branch".

### 4b. New codebase

1. Determine the base directory (check in order, first match wins):
   1. CWD is `$HOME` or `$HOME/src` -> base = CWD.
   2. Inside a git repo -> base = parent of the repo root
      (`git rev-parse --show-toplevel`, then one level up).
   3. Otherwise -> base = CWD.
2. Candidate directory: `<base>/<repo-name>`. If it already exists, append
   `-2`, `-3`, ... until unique.
3. Confirm the location with the user before continuing.
4. `mkdir -p <base>/<repo-name>/.stories`
5. `cd` into the new directory. Before running `git init`, verify you are
   not inside someone else's repo:
   ```bash
   git rev-parse --show-toplevel 2>/dev/null
   ```
   If this prints a path *above* the new directory (the candidate is nested
   inside an existing repo), **STOP** and ask the user whether to proceed
   with a nested repo, pick a different base, or abort. Otherwise run
   `git init`.
6. **No code is written.** Implementation is for `/arc-maestro` or a
   developer once the stories exist.

## Step 5: Artifact Generation

### 5.1 Story-ID prefix

Auto-generate from the feature slug. The algorithm is deterministic --
follow each rule exactly.

1. Split the slug on `-` -> `words`.
2. **Remove purely numeric words.** A word is purely numeric only if *every*
   character is `[0-9]`. Mixed alphanumeric words (`v2`, `2fa`, `h264`,
   `3d`) are **retained**. Example: slug `404-error-page` -> `404` is
   dropped -> words become `["error", "page"]` -> prefix `EP`.
3. `prefix = uppercase(first letter of each remaining word)`.
4. **Edge cases**:
   - **Single-word slug** (e.g., `billing`): extend with the next two
     letters -> `BIL`. If the word has fewer than 3 characters (e.g.,
     `ui`), use the full word uppercased -> `UI`. This also covers slugs
     starting with digits but containing letters (e.g., `2fa` is one
     non-numeric word -> `2FA`).
   - **Empty `words` after step 2** (every word was purely numeric, e.g.,
     `404` or `2024-07`): fall back to the first 3 alphanumeric characters
     of the slug, uppercased -> `404` stays `404`, `2024-07` -> `202`.
5. **Collision handling**: list existing `<PREFIX>-NNNN.md` files in
   `.stories/`. Branch on **ownership**:

   - **Same-feature re-run** -- `.stories/feature-<slug>.md` exists AND
     `<PREFIX>-NNNN.md` files exist. This prefix belongs to the current
     feature:
     - Do NOT change the prefix.
     - Scan `.stories/<PREFIX>-*.md`, find the highest `NNNN`, and start
       new numbering at `max(NNNN) + 1`.
     - Tell the user: "Appending to the existing `<PREFIX>` backlog,
       starting at `<PREFIX>-<max+1>`."
     - The three feature-level docs (`feature-<slug>.md`, `-prd.md`,
       `-technical-design.md`) are **rewritten** to reflect the updated
       scope (the checklist in `feature-<slug>.md` must include the new
       stories). This is an explicit exception to the "do not touch
       existing `.stories/` files" rule. Existing individual
       `<PREFIX>-NNNN.md` files from prior runs are NOT rewritten.

   - **Different-feature collision** -- `<PREFIX>-NNNN.md` files exist
     and another `feature-*.md` in `.stories/` references them (scan each
     `feature-*.md` for the prefix in its story checklist). The owning
     feature has a different slug. Make the prefix unique by appending
     digits: `<PREFIX>2`, `<PREFIX>3`, etc. **Always append digits** --
     never extend with additional letters. Inform the user of the change.

   - **Partial prior run** -- `<PREFIX>-NNNN.md` files exist,
     `.stories/feature-<slug>.md` is missing, AND no other `feature-*.md`
     claims ownership of those files (i.e., the different-feature check
     above found nothing). This indicates a previous run that failed
     mid-write. Do NOT silently mutate to `<PREFIX>2`. Stop and ask the
     user: "I found existing `<PREFIX>-NNNN.md` files but no
     `feature-<slug>.md`. Should I adopt `<PREFIX>` and continue from
     `max(NNNN) + 1`, or start fresh with a new prefix?" Act on the answer.

   - **No collision** -- no `<PREFIX>-NNNN.md` files exist. Proceed with
     the derived prefix unchanged.
6. **Initial numbering** starts at `1001` and increments by one per story
   (4-digit padding). Re-runs use `max(NNNN) + 1` as described above.

Examples:
- `two-factor-auth` -> `TFA`, stories `TFA-1001`, `TFA-1002`, ...
- `billing` -> `BIL`
- `2fa` -> `2FA` (single mixed-alphanumeric word, extended to 3 chars)
- `404-error-page` -> `EP` (purely numeric `404` dropped)
- `2024-07` -> `202` (all words numeric, fallback to first 3 alphanumerics)

### 5.2 Individual story files

For each story agreed in Step 3, write `.stories/<PREFIX>-<1001+idx>.md`
using this template:

```markdown
# <PREFIX>-<NNNN>: <Story Title>

## Overview

<1-2 paragraph summary: what this story delivers and why.>

**Repos:** <repo names this story touches>
**Feature branch (<repo>):** <branch name or "n/a"> -- story branches base
off this and merge back to this, NOT to main/development.
**Story branch:** <suggested branch name, e.g., `<prefix-lowercase>-nnnn-short-desc`>

## Reference Material

- <Source doc title> -- `.stories/docs/<filename>` (copied from <original path>)
- <Linked tickets, research docs, Figma links, etc.>

## Architecture

<Prose description of the change. Include ASCII flow diagrams where they
help (current state -> target state). For small stories one paragraph is
sufficient. For larger ones, cover data flow, component boundaries, and
non-obvious interactions.>

## Acceptance Criteria

### 1. <Logical Group Name>

- [ ] <Concrete, testable criterion>
- [ ] <Concrete, testable criterion>

### 2. <Logical Group Name>

- [ ] <Concrete, testable criterion>

## Implementation Guidance

<Gotchas, conventions to follow, files to study, patterns from the
codebase to reuse. Real file paths from `Glob` / `Grep` searches during
Step 3 belong here.>

## Testing

- [ ] Unit: <what>
- [ ] Integration: <what>
- [ ] Manual: <what, if applicable>

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| <risk> | <mitigation> |

## Dependencies

- **Blocks:** <story IDs this unblocks, or "Nothing">
- **Blocked by:** <story IDs that must complete first, or "Nothing">
```

Acceptance criteria use `- [ ]` so they serve as a natural checklist for the
implementer.

### 5.3 `.stories/feature-<slug>.md` -- overview and checklist

All three feature-level docs live in `.stories/` alongside the story files.
Internal links are relative to siblings.

```markdown
# Feature: <Feature Name>

<One-paragraph elevator pitch. What problem this addresses, who benefits,
and the general shape of the solution.>

**Repos:** <repo names>
**Feature branch:** <branch name or "n/a">
**Related docs:**
- [Product Requirements](feature-<slug>-prd.md)
- [Technical Design](feature-<slug>-technical-design.md)

## Stories

- [ ] [<PREFIX>-1001](<PREFIX>-1001.md) -- <one-line title>
- [ ] [<PREFIX>-1002](<PREFIX>-1002.md) -- <one-line title>
...

## Status

All stories: **todo**.

## Source Material

<List of files copied into docs/ (relative to .stories/), OR "Inline
description (no attached files) -- preserved in docs/feature-<slug>-source.md"
if the argument was inline text.>
```

### 5.4 `.stories/feature-<slug>-prd.md` -- product requirements

Oriented toward the development team. Sections:

- **User need** -- the pain this addresses, grounded in real scenarios.
- **Goals and non-goals** -- what is in scope, what is explicitly out.
- **Personas and stakeholders** -- who uses this, who reviews, who approves.
- **User stories and flows** -- narrative walk-throughs mapped to story IDs.
  "As a <persona>, I want <capability> so that <outcome>."
- **Functional requirements** -- what the feature must do, stated in
  implementation-neutral language.
- **Feature-level acceptance criteria** -- criteria that span the full
  feature, not individual stories (those live in the story files).
- **UX notes and references** -- source doc paths, screenshots, Figma links.
- **Dependencies** -- teams, services, APIs, vendor relationships.
- **Risks and open questions** -- unresolved items requiring a human decision.

**Explicitly omit**: cost analysis, competitive analysis, go-to-market
plans, pricing. These are outside the scope of a dev-team-facing document.

### 5.5 `.stories/feature-<slug>-technical-design.md`

Sections:

- **Summary** -- one paragraph connecting the PRD's outcomes to the
  technical approach.
- **Architecture** -- current state -> target state, prose and ASCII
  diagrams where useful.
- **Data model changes** -- new entities, modified entities, migrations.
- **API and interface changes** -- new endpoints, modified payloads, new
  frontend globals, new events.
- **Component breakdown** -- modules or services added or changed, and
  how they interact.
- **Security and authorization** -- new auth flows, permission model
  changes, multi-tenancy considerations, feature flag gating.
- **Performance and scalability** -- anticipated hotspots, load patterns,
  caching strategies.
- **Observability** -- logs, metrics, alerts to add.
- **Rollout plan and feature flags** -- flag names, default values,
  opt-in vs opt-out, safety nets.
- **Testing strategy** -- unit / integration / E2E breakdown; any test
  infrastructure changes needed.
- **Open technical questions** -- anything unresolved.
- **Reference material** -- table of existing files in the repo worth
  studying, populated with real paths from Step 3 using `Glob` and `Grep`.

### 5.6 Source material preservation

1. `mkdir -p .stories/docs`
2. For every input file, copy it to `.stories/docs/<original-basename>`
   with **idempotent collision handling**. Determine the state with concrete
   commands -- do not guess. Check in order:
   - `test ! -e "$dest"` -> copy.
   - `test -d "$dest"` -> **STOP**: "Destination `$dest` is a directory,
     not a file. Please resolve manually." Do not run `cmp` on a directory.
   - `cmp --silent "$src" "$dest"` returns 0 (byte-identical) -> skip
     silently (re-run; nothing to do).
   - `cmp` returns non-zero (content differs) -> ask the user: "Overwrite,
     rename the new copy with a `-2` suffix, or skip?" Act on the answer.
   - Never silently create numbered duplicates.
3. If `source_type == "inline"`, write the original `$ARGUMENTS` text to
   `.stories/docs/feature-<slug>-source.md` (same idempotency rules).
4. If the source material references images or PDFs that resolve to a
   findable path on disk, copy those too (same rules). If a referenced file
   cannot be located, list it in the PRD under "Risks and open questions".

### 5.7 Final directory layout

```
<repo>/
└── .stories/
    ├── feature-<slug>.md
    ├── feature-<slug>-prd.md
    ├── feature-<slug>-technical-design.md
    ├── <PREFIX>-1001.md
    ├── <PREFIX>-1002.md
    ├── ...
    └── docs/
        └── <copied source files>
```

All paths in Step 5 are relative to the repo directory established in Step 4.

## Step 6: Review and Approval

1. Show the generated file tree with `ls -R <repo>/.stories/`.
2. Display the contents of `.stories/feature-<slug>.md` (the shortest of
   the three feature-level docs).
3. Say: "You can request changes if anything needs adjustment."
4. **Approval loop**: ask "Do you approve the backlog?"
   - If the user requests edits: apply them, re-show the affected file(s),
     and re-ask. Keep `$LAUNCH_DIR/.maestro-feature-scratch.md` during this
     loop -- if the edits require returning to Step 3 (new story, changed
     scope, renamed slug), use it as context and loop back.
   - Only exit when the user explicitly approves.
5. **After approval**: delete `$LAUNCH_DIR/.maestro-feature-scratch.md`.
6. Print next-step guidance:

```
Backlog ready (in <repo>/.stories/):
  feature-<slug>.md
  feature-<slug>-prd.md
  feature-<slug>-technical-design.md
  <PREFIX>-1001.md ... <PREFIX>-<last>.md

Next steps:
  1. cd <repo>
  2. /arc-maestro-vet-stories       -- audit the backlog for gaps
  3. git checkout -b <feature-branch>   (if you chose a feature branch)
  4. /arc-maestro .stories/<PREFIX>-1001.md   -- begin implementing the first story

Note: The `.stories/` directory is dot-prefixed. If you want it excluded
from version control, add `/.stories/` to `.gitignore`. This skill does
NOT modify `.gitignore` -- decide whether the backlog should be committed
or kept private.
```

## Important Notes

- This skill ONLY generates backlog artifacts. It does NOT implement the
  feature. Implementation is for `/arc-maestro` or a developer.
- Stories should be detailed enough that a developer can build from them
  without the original source documents.
- **Disregard time estimates** in source docs -- do not generate, repeat,
  or validate them. Flag only if overall scope appears multi-quarter.
- **Scratch file cleanup**: always delete
  `$LAUNCH_DIR/.maestro-feature-scratch.md` after Step 6 approval. Use
  `$LAUNCH_DIR`, never the current CWD -- Step 4 changes directories.
- **Do not touch existing `.stories/` files.** Add alongside them.
  **Exception:** same-feature re-runs (Step 5.1 rule 5) rewrite the three
  feature-level docs so the backlog stays accurate. Individual
  `<PREFIX>-NNNN.md` files from prior runs are never modified.
- **Do not modify `.gitignore`.** Surface the question in the final output
  so the user decides.
- **Do not create git branches.** Surface suggested names; the user runs
  `git checkout -b`.
- **Do not clone without confirmation.** Always ask before running
  `git clone`.
