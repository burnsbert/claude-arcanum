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

---

## Verification

After installation, verify everything is in place:

```bash
# Check installed commands
ls ~/.claude/commands/arc-* ~/.claude/commands/ca-*

# Check installed agents
ls ~/.claude/agents/arc-* ~/.claude/agents/ca-*
```

You should see:

**Commands:**
- arc-investigate.md
- arc-llm.md
- arc-pr-respond.md
- arc-pr-review.md
- arc-rca.md
- ca-store-problem-context.md

**Agents:**
- arc-deep-research.md
- arc-root-cause-analyzer.md
- ca-brainstormer.md
- ca-code-review-validator.md
- ca-problem-theory-validator.md

---

## Testing Your Installation

### Test a Command

Open a new Claude Code session and try:

```bash
/arc-investigate
```

If you see output asking for a problem description, the command is installed correctly!

### Test an Agent

In a Claude Code session:

```
Use the arc-deep-research agent to investigate:

ultrathink

Question: What files exist in this repository?
```

If the agent responds with research methodology steps, it's working!

---

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

## Understanding What You Installed

### User-Facing Commands (arc-*)

These are what you'll invoke directly:

- **`/arc-investigate`** - Debug problems with theory validation
- **`/arc-rca`** - Root cause analysis after fixing bugs
- **`/arc-llm`** - Generate prompts for external LLMs
- **`/arc-pr-review`** - Review GitHub PRs with validation
- **`/arc-pr-respond`** - Respond to PR feedback with validation

### Utility Commands (ca-*)

These are called automatically by other commands:

- **`/ca-store-problem-context`** - Extracts problem context (used by arc-investigate, arc-llm)

### User-Facing Agents (arc-*)

These you can invoke directly via Task tool:

- **`arc-root-cause-analyzer`** - Forensic bug analysis (also used by /arc-rca)
- **`arc-deep-research`** - Four-step research methodology

### Utility Agents (ca-*)

These are called automatically by commands/agents:

- **`ca-brainstormer`** - Generates theories (used by arc-investigate)
- **`ca-problem-theory-validator`** - Validates theories (used by arc-investigate)
- **`ca-code-review-validator`** - Vets PR feedback (used by arc-pr-review, arc-pr-respond)

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

## Troubleshooting

### GitHub CLI errors

If `/arc-pr-review` or `/arc-pr-respond` fail with "gh: command not found":
1. Install GitHub CLI (see [Prerequisites](#prerequisites))
2. Authenticate: `gh auth login`
3. Test it works: `gh pr list` in a GitHub repository

If you get authentication errors:
```bash
# Re-authenticate
gh auth login

# Check authentication status
gh auth status
```

### Command not found

If `/arc-investigate` doesn't work:
1. Check the file exists: `ls ~/.claude/commands/arc-investigate.md`
2. Restart Claude Code or start a new session
3. Verify the file has correct YAML frontmatter (description field)

### Agent not found

If "Use the arc-deep-research agent" doesn't work:
1. Check the file exists: `ls ~/.claude/agents/arc-deep-research.md`
2. Verify the file has correct YAML frontmatter (name, description, tools, color)
3. Try using the full prompt format from the README

### Permission issues

If you get permission errors:
```bash
# Make sure the directories exist
mkdir -p ~/.claude/commands ~/.claude/agents

# Try installation again
cp commands/*.md ~/.claude/commands/
cp agents/*.md ~/.claude/agents/
```

---

## Platform-Specific Notes

### macOS / Linux

The instructions above work as-is.

### Windows (WSL)

If using Claude Code in WSL:
```bash
# Use WSL paths
cp commands/*.md ~/.claude/commands/
cp agents/*.md ~/.claude/agents/
```

### Windows (Native)

If using Claude Code natively on Windows:
```powershell
# Use PowerShell
Copy-Item commands\*.md $env:USERPROFILE\.claude\commands\
Copy-Item agents\*.md $env:USERPROFILE\.claude\agents\
```

---

## What's Next?

After installation:

1. **Read the [README.md](README.md)** for detailed documentation on each command and agent
2. **Try `/arc-investigate`** on your next bug
3. **Use `/arc-pr-review`** on your next code review
4. **Explore `arc-deep-research`** for complex technical questions

For questions or issues, see the [README.md](README.md) for more information.
