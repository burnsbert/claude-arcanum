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

## Quick Install (Recommended)

Copy all commands and agents to your global Claude Code configuration:

```bash
# From the claude-arcanum directory
cp commands/*.md ~/.claude/commands/
cp agents/*.md ~/.claude/agents/
```

Done! All commands and agents are now available in any Claude Code session.

---

## Manual Installation (Step by Step)

If you prefer to install selectively or understand what's being installed:

### Step 1: Install Commands

Commands are invoked with `/command-name` in Claude Code.

```bash
# Install all commands
cp commands/arc-investigate.md ~/.claude/commands/
cp commands/arc-rca.md ~/.claude/commands/
cp commands/arc-llm.md ~/.claude/commands/
cp commands/arc-pr-review.md ~/.claude/commands/
cp commands/arc-pr-respond.md ~/.claude/commands/
cp commands/ca-store-problem-context.md ~/.claude/commands/
```

**Or install selectively:**
```bash
# Just the PR workflow commands
cp commands/arc-pr-review.md ~/.claude/commands/
cp commands/arc-pr-respond.md ~/.claude/commands/

# Just the debugging commands
cp commands/arc-investigate.md ~/.claude/commands/
cp commands/arc-rca.md ~/.claude/commands/
```

### Step 2: Install Agents

Agents are invoked via the Task tool and provide specialized intelligence.

```bash
# Install all agents
cp agents/arc-root-cause-analyzer.md ~/.claude/agents/
cp agents/arc-deep-research.md ~/.claude/agents/
cp agents/ca-brainstormer.md ~/.claude/agents/
cp agents/ca-problem-theory-validator.md ~/.claude/agents/
cp agents/ca-code-review-validator.md ~/.claude/agents/
```

**Or install selectively:**
```bash
# Just user-facing agents (arc-*)
cp agents/arc-root-cause-analyzer.md ~/.claude/agents/
cp agents/arc-deep-research.md ~/.claude/agents/

# Note: ca-* agents are automatically used by arc-* commands/agents
# You typically want all agents even if you're selective about commands
```

## What Gets Installed Where

```
~/.claude/
├── commands/           # Slash commands (/command-name)
│   ├── arc-investigate.md
│   ├── arc-rca.md
│   ├── arc-llm.md
│   ├── arc-pr-review.md
│   ├── arc-pr-respond.md
│   └── ca-store-problem-context.md
│
└── agents/             # Task tool agents
    ├── arc-root-cause-analyzer.md
    ├── arc-deep-research.md
    ├── ca-brainstormer.md
    ├── ca-problem-theory-validator.md
    └── ca-code-review-validator.md
```

**Note**: The `.claude/` directory is in your home directory and is used by Claude Code globally across all projects.

---

## Updating

To update to the latest version:

```bash
# Pull latest changes
cd /path/to/claude-arcanum
git pull

# Reinstall (overwrites existing files)
cp commands/*.md ~/.claude/commands/
cp agents/*.md ~/.claude/agents/
```

---

## Uninstalling

To remove Claude Arcanum:

```bash
# Remove all commands
rm ~/.claude/commands/arc-*.md
rm ~/.claude/commands/ca-*.md

# Remove all agents
rm ~/.claude/agents/arc-*.md
rm ~/.claude/agents/ca-*.md
```

---

For questions or issues, see the [README.md](README.md) for more information.
