# Installation Guide

This guide walks you through installing Claude Arcanum commands and agents for use in Claude Code.

## Prerequisites

### GitHub CLI (Required for PR Commands)

The `/arc-pr-review` and `/arc-pr-respond` commands require the GitHub CLI (`gh`) to fetch PR data from GitHub.

**Good news**: These commands will automatically detect if `gh` is missing and offer to install it for you! They support:

- **macOS** - Auto-installs via Homebrew
- **Linux** - Auto-detects apt/dnf/pacman and installs
- **Windows** - Auto-detects winget/Chocolatey/Scoop and installs

**Manual Installation** (if you prefer):

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt install gh

# Fedora/RHEL
sudo dnf install gh

# Arch
sudo pacman -S github-cli
```

**Windows:**
```powershell
# Using winget (built-in on Windows 11/10)
winget install GitHub.cli

# Using Chocolatey
choco install gh -y

# Using Scoop
scoop install gh
```

**After installation, authenticate:**
```bash
gh auth login
```

**Note**: If you don't plan to use the PR review commands (`/arc-pr-review` and `/arc-pr-respond`), you can skip installing `gh`. All other commands and agents work without it.

---

## Plugin Installation (Recommended)

The easiest way to install Claude Arcanum is as a Claude Code plugin.

### From GitHub

```bash
# Step 1: Add the marketplace
/plugin marketplace add burnsbert/claude-arcanum

# Step 2: Install the plugin
/plugin install arcanum
```

### Local Installation (For Development/Testing)

If you've cloned the repository locally:

```bash
# From any directory, reference the path to claude-arcanum
/plugin install /path/to/claude-arcanum

# Or if you're already in the claude-arcanum directory
/plugin install .
```

### Using the Plugin UI

You can also install via the Claude Code plugin interface:

1. Type `/plugin` in Claude Code
2. Select "Add Marketplace"
3. Enter: `burnsbert/claude-arcanum`
4. Then browse and install "arcanum"

### Managing the Plugin

```bash
# Check if installed
/plugin
# Then select: 5. View installation status

# To manage plugins
/plugin
# Then select: 2. Manage and uninstall plugins

# From there you can:
# - Disable/enable plugins
# - Uninstall plugins
# - Update to latest versions
```

Done! All commands and agents are now available in any Claude Code session.

---

## Manual Installation (Alternative Method)

If you prefer manual installation or want to install selectively, use **symlinks** so updates to the repo automatically propagate without re-copying.

### Quick Manual Install

Symlink all commands, agents, and skills to your global Claude Code configuration:

```bash
# From the claude-arcanum directory
ARCANUM_DIR="$(pwd)"

# Create target directories if they don't exist
mkdir -p ~/.claude/commands ~/.claude/agents/personalities ~/.claude/skills

# Symlink commands
for f in "$ARCANUM_DIR"/commands/*.md; do
  ln -sf "$f" ~/.claude/commands/
done

# Symlink agents
for f in "$ARCANUM_DIR"/agents/*.md; do
  ln -sf "$f" ~/.claude/agents/
done

# Symlink personality definitions
for f in "$ARCANUM_DIR"/agents/personalities/*.md; do
  ln -sf "$f" ~/.claude/agents/personalities/
done

# Symlink skills
for d in "$ARCANUM_DIR"/skills/*/; do
  ln -sf "$d" ~/.claude/skills/
done
```

Done! All commands and agents are now available in any Claude Code session, and pulling updates to the repo automatically updates your installation.

### Selective Installation

If you want to install specific toolkits:

#### Debugging & Investigation

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-investigate.md ~/.claude/commands/
ln -sf "$ARCANUM_DIR"/commands/arc-rca.md ~/.claude/commands/
ln -sf "$ARCANUM_DIR"/commands/ca-store-problem-context.md ~/.claude/commands/

# Agents
ln -sf "$ARCANUM_DIR"/agents/arc-root-cause-analyzer.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-brainstormer.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-problem-theory-validator.md ~/.claude/agents/
```

#### PR Review

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-pr-review.md ~/.claude/commands/
ln -sf "$ARCANUM_DIR"/commands/arc-pr-respond.md ~/.claude/commands/

# Agents
ln -sf "$ARCANUM_DIR"/agents/ca-code-review-validator.md ~/.claude/agents/
```

#### LLM Consultation & Prompt Engineering

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

ln -sf "$ARCANUM_DIR"/commands/arc-llm.md ~/.claude/commands/
```

#### Research Team & Deep Research

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-research-team.md ~/.claude/commands/

# Agents
ln -sf "$ARCANUM_DIR"/agents/arc-deep-research.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-research-agent.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-research-synthesizer.md ~/.claude/agents/
```

#### War Room

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-war-room.md ~/.claude/commands/

# Agents (also needs debugging agents above)
ln -sf "$ARCANUM_DIR"/agents/ca-war-room-investigator.md ~/.claude/agents/
```

#### Think Tank

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-think-tank.md ~/.claude/commands/

# Agents
ln -sf "$ARCANUM_DIR"/agents/ca-think-tank-thinker.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-think-tank-vetter.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-think-tank-riffer.md ~/.claude/agents/
ln -sf "$ARCANUM_DIR"/agents/ca-think-tank-judge.md ~/.claude/agents/

# Personality definitions
mkdir -p ~/.claude/agents/personalities
for f in "$ARCANUM_DIR"/agents/personalities/*.md; do
  ln -sf "$f" ~/.claude/agents/personalities/
done
```

#### Maestro (Semi-Autonomous Development)

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

# Commands
ln -sf "$ARCANUM_DIR"/commands/arc-maestro.md ~/.claude/commands/
ln -sf "$ARCANUM_DIR"/commands/arc-maestro-review.md ~/.claude/commands/

# All Maestro agents
for f in "$ARCANUM_DIR"/agents/ca-maestro-*.md; do
  ln -sf "$f" ~/.claude/agents/
done
```

#### Technical Writing

```bash
ARCANUM_DIR="/path/to/claude-arcanum"

ln -sf "$ARCANUM_DIR"/agents/arc-technical-writer.md ~/.claude/agents/
```

**Note**: `ca-*` agents are internal utilities used by `arc-*` commands. If you install a command, install all its dependent agents too (listed in the toolkit sections above).

## What Gets Installed Where

```
~/.claude/
├── commands/                              # Slash commands (/command-name)
│   ├── arc-investigate.md                 # Automated troubleshooting
│   ├── arc-rca.md                         # Root cause analysis
│   ├── arc-llm.md                         # External LLM consultation
│   ├── arc-pr-review.md                   # PR code review
│   ├── arc-pr-respond.md                  # PR review response
│   ├── arc-research-team.md               # Team-based parallel research
│   ├── arc-war-room.md                    # Team-based investigation
│   ├── arc-think-tank.md                  # Creative ideation
│   ├── arc-maestro.md                     # Semi-autonomous development
│   ├── arc-maestro-review.md              # Maestro code review + PR
│   └── ca-store-problem-context.md        # Problem context utility
│
├── agents/                                # Task tool agents
│   ├── arc-root-cause-analyzer.md         # Git forensics + RCA
│   ├── arc-deep-research.md               # Four-step deep research
│   ├── arc-technical-writer.md            # Technical documentation
│   ├── ca-brainstormer.md                 # Theory generation
│   ├── ca-problem-theory-validator.md     # Theory validation
│   ├── ca-code-review-validator.md        # Code review feedback vetting
│   ├── ca-research-agent.md               # Research team member
│   ├── ca-research-synthesizer.md         # Research synthesis
│   ├── ca-war-room-investigator.md        # War room investigator
│   ├── ca-think-tank-thinker.md           # Idea generation
│   ├── ca-think-tank-vetter.md            # Idea evaluation
│   ├── ca-think-tank-riffer.md            # Idea evolution
│   ├── ca-think-tank-judge.md             # Final idea ranking
│   ├── ca-maestro-scout.md                # Codebase researcher
│   ├── ca-maestro-planner.md              # Task decomposer
│   ├── ca-maestro-plan-reviewer.md        # Plan quality gate
│   ├── ca-maestro-junior-dev-doer.md      # Junior implementer (Haiku)
│   ├── ca-maestro-dev-doer.md             # Standard implementer (Sonnet)
│   ├── ca-maestro-senior-dev-doer.md      # Senior implementer (Opus)
│   ├── ca-maestro-frontend-dev-doer.md    # Frontend specialist (Opus)
│   ├── ca-maestro-devops-dev-doer.md      # DevOps specialist (Opus)
│   ├── ca-maestro-task-validator.md       # Standard validator (Haiku)
│   ├── ca-maestro-senior-task-validator.md # Senior validator (Sonnet)
│   ├── ca-maestro-ui-validator.md         # Visual UI validator (Opus)
│   ├── ca-maestro-code-review.md          # Maestro code review
│   ├── ca-maestro-code-review-responder.md # Maestro review responder
│   └── personalities/                     # Think-tank personalities
│       ├── contrarian.md
│       ├── pragmatist.md
│       ├── visionary.md
│       └── connector.md
│
└── skills/                                # Conversational skills
    └── rubber-duck/
        └── SKILL.md
```

**Note**: The `~/.claude/` directory is in your home directory and is used by Claude Code globally across all projects.

---

## Updating

With symlink installation, just pull the latest changes:

```bash
cd /path/to/claude-arcanum
git pull
```

That's it — symlinks automatically pick up the updated files.

If you used the copy method previously and want to switch to symlinks:

```bash
# Remove old copies
rm ~/.claude/commands/arc-*.md ~/.claude/commands/ca-*.md
rm ~/.claude/agents/arc-*.md ~/.claude/agents/ca-*.md

# Then follow the Quick Manual Install above
```

---

## Uninstalling

To remove Claude Arcanum:

```bash
# Remove all command symlinks/files
rm ~/.claude/commands/arc-*.md
rm ~/.claude/commands/ca-*.md

# Remove all agent symlinks/files
rm ~/.claude/agents/arc-*.md
rm ~/.claude/agents/ca-*.md
rm -rf ~/.claude/agents/personalities/

# Remove skills
rm -rf ~/.claude/skills/rubber-duck/
```

---

For questions or issues, see the [README.md](README.md) for more information.
