---
name: skill-discovery
description: Discover and install agent skills from the skills.sh marketplace. Use when user asks "find a skill for X", "is there a skill for Y", or wants to extend agent capabilities with existing skills.
---

# Skill Discovery

Discover and install skills from the open agent skills ecosystem at skills.sh.

## When to Use

- User asks "find a skill for X"
- User says "is there a skill that can..."
- User wants to extend capabilities with existing tools
- User asks "how do I do X with an agent"

## Skills CLI Commands

```bash
# Search for skills
npx skills find [query]

# Install a skill
npx skills add [owner/repo@skill-name] --yes

# Check installed skills
npx skills check

# Update all skills
npx skills update
```

## Workflow

1. **Search first** — `npx skills find [topic]`
2. **Check leaderboard** — https://skills.sh/ for popular skills
3. **Install with --yes** — `npx skills add owner/repo@skill --yes`
4. **Symlink to agents** — Skills auto-symlink to supported agents

## Example Searches

```bash
# Humanizer
npx skills find humanizer

# Browser automation
npx skills find browser

# Code review
npx skills find review

# Testing
npx skills find testing
```

## Popular Skill Sources

| Source | URL | Notable Skills |
|--------|-----|----------------|
| addyosmani/agent-skills | GitHub | 21 engineering skills |
| mattpocock/skills | GitHub | Real engineer workflows |
| vercel-labs/skills | GitHub | find-skills |
| softaworks/agent-toolkit | GitHub | 43 tools incl humanizer |
| ComposioHQ/awesome-codex-skills | GitHub | 40+ Codex skills |

## Installation Notes

- Skills install to `~/.agents/skills/`
- Auto-symlink to supported agents (OpenClaw, Claude Code, Codex, etc.)
- Use `--yes` flag to skip interactive prompts
- Security assessment shown during install (Gen, Socket, Snyk)