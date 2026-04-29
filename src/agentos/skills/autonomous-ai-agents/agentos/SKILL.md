---
name: agentos
description: AgentOS CLI - Autonomous agent framework with ROMA planning, HTAA tool grouping, MOSAIC safety, InfiAgent memory, and REDEREF reflection. Use for complex task automation.
---

# AgentOS CLI

Open-source autonomous agent framework combining 9+ AI agent papers from 2026.

## Installation

```bash
cd /opt/agentos && uv pip install -e . --system
```

## Commands

```bash
# Run a task
agentos run "Build a REST API for todo list"

# Interactive wizard
agentos wizard

# List sessions
agentos sessions

# Resume session
agentos resume --session session_id

# Delete session
agentos delete --session session_id

# Info
agentos info
```

## Architecture

```
Input → Context Eng → ROMA Planner → HTAA Executor → MOSAIC Safety → Memory → Reflection
```

## Papers Integrated

- ROMA - Recursive task decomposition
- INTENT - Budget-aware planning
- HTAA - Tool grouping
- ToolTree - MCTS planning
- MOSAIC - Safety-first
- InfiAgent - File state
- ChromaDB - Vector memory
- REDEREF - Reflection learning
