---
name: fikriaf-agentos
description: AgentOS from fikriaf/agentos - Autonomous AI agent framework with ROMA planning, HTAA tool grouping, MOSAIC safety. Use for complex task automation.
---

# AgentOS (fikriaf/agentos)

Autonomous AI agent framework from https://github.com/fikriaf/agentos

## Installation

```bash
git clone https://github.com/fikriaf/agentos.git /opt/agentos
cd /opt/agentos
pip install -e .
```

## Requirements

- Python 3.10+
- OpenAI API key (or compatible)
- Skills in `~/.hermes/skills/`

## Configuration

Set environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

Or use config file at `~/.agentos/config.yaml`:
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
```

## Commands

```bash
# Run task (auto mode)
agentos run "Build a REST API for todo list"

# Interactive wizard mode
agentos wizard

# Session management
agentos sessions          # List sessions
agentos resume --session session_id
agentos delete --session session_id

# Info
agentos info
```

Quick mode with auto-confirm:
```bash
agentos run "Write tests" --auto-confirm
```

## Architecture

```
User Input → Context Engineering → ROMA Planner → HTAA Executor → MOSAIC Safety → Memory → Reflection
```

### Components

1. **ROMA Planner** - Recursive task decomposition into parallel subtasks
2. **HTAA Executor** - Tool grouping for reduced action space
3. **MOSAIC Safety** - Plan → Check → Act/Refuse safety pipeline
4. **Memory** - File-based state externalization (InfiAgent)
5. **Skills** - 93 built-in skills loaded on demand

## Key Files

- `src/agentos/cli.py` - Main CLI entry point
- `src/agentos/agents/planner.py` - ROMA planner implementation
- `src/agentos/agents/executor.py` - HTAA executor with tool grouping
- `src/agentos/skills/__init__.py` - SkillsManager loader
- `SPEC.md` - Full technical specification

## Skills Integration

Copy existing skills to AgentOS:
```bash
cp -r ~/.hermes/skills/* /opt/agentos/src/agentos/skills/
cd /opt/agentos && pip install -e .
```

AgentOS loads skills via `skill_view(name)` for context.

## Known Issues

| Issue | Solution |
|-------|----------|
| Safety blocks startup | Use `--auto-confirm` flag |
| Python tool fails | Use `python3` not `python` in commands |

## Troubleshooting

```bash
# Debug mode
agentos run "task" --verbose

# Check version
agentos --version

# Show config
agentos info
```

## Links

- GitHub: https://github.com/fikriaf/agentos
- Releases: https://github.com/fikriaf/agentos/releases
- Author: fikriaf