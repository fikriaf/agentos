---
name: mattpocock-skills
description: Engineering skills for real-world coding agents. Use for grilling sessions before development, TDD, code architecture, issue triage, and PRD creation. Based on decades of engineering experience.
---

# Matt Pocock's Skills for Real Engineers

Skills for coding agents from https://github.com/mattpocock/skills (37k stars)

## Philosophy
Small, composable skills that give you control. Based on decades of engineering experience.

## Available Skills

### Engineering
- `grill-with-docs` — Detailed requirements gathering with shared language creation
- `tdd` — Test-driven development workflow
- `improve-codebase-architecture` — Refactor and improve code structure
- `diagnose` — Debug issues systematically
- `to-issues` — Convert tasks to actionable issues
- `to-prd` — Create Product Requirements Documents
- `triage` — Triage issues using labels
- `zoom-out` — Get high-level perspective on codebase

### Productivity
- `grill-me` — Quick requirements gathering session
- `caveman` — Minimal viable debugging
- `write-a-skill` — Create new skills for agents

## Quick Start

```bash
# For Claude Code / Codex
npx skills@latest add mattpocock/skills
```

## Key Concepts

### Grill Session
Before any significant work, do a "grilling session" to align:
- What exactly are we building?
- What jargon exists in this domain?
- What are the edge cases?

### Shared Language
Create a `CONTEXT.md` file with domain-specific jargon:
- BEFORE: "There's a problem when a lesson inside a section of a course is made 'real'"
- AFTER: "There's a problem with the materialization cascade"

### Small Steps
Always take small, deliberate steps. The rate of feedback is your speed limit.

## Location
Installed at: /opt/skills