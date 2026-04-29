# AgentOS

<p align="center">
  <a href="https://github.com/fikriaf/agentos">
    <img src="https://img.shields.io/badge/GitHub-fikriaf/agentos-blue.svg" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/Version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/Agents-Research-red.svg" alt="Type">
</p>

> **AgentOS** — An autonomous AI agent framework built on cutting-edge research. Built by [fikriaf](https://github.com/fikriaf).

## 🎯 Overview

AgentOS is an **autonomous agent operating system** that integrates 9 state-of-the-art AI agent papers into a production-ready CLI framework. It provides:

- 🔄 **Recursive Task Decomposition** — Break complex tasks into parallel subtasks
- 🛡️ **Safety-First Execution** — MOSAIC-style Plan→Check→Act/Refuse
- 💰 **Budget-Aware Planning** — INTENT-style cost estimation
- 🧠 **Long-Horizon Memory** — File-based state externalization (InfiAgent)
- 🔧 **93 Built-in Skills** — Ready-to-use specialized knowledge

## 📐 Architecture

![AgentOS Architecture](docs/agentos-architecture.png)

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              CONTEXT LAYER (Context Engineering)              │
│  • 93 built-in skills                                       │
│  • Task-aware skill loading                                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              PLANNING LAYER (ROMA + INTENT)                   │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │ ROMA Planner      │    │ INTENT Budget Tracker       │    │
│  │ Task decomp       │    │ Cost estimation            │    │
│  │ Parallel groups   │    │ Budget constraints         │    │
│  └──────────────────┘    └───────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              EXECUTION LAYER (HTAA + ToolTree)               │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │ HTAA Executor     │    │ ToolTree Planner           │    │
│  │ Tool grouping     │    │ MCTS-inspired planning     │    │
│  │ Reduced action    │    │ Dual-feedback evaluation   │    │
│  │ space            │    │                           │    │
│  └──────────────────┘    └───────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              SAFETY LAYER (MOSAIC)                           │
│  Plan → Check → Act/Refuse                                  │
│  • Risk screening        • Refusal as first-class action    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              REFLECTION LAYER (REDEREF + Deep Researcher)     │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │ REDEREF Router   │    │ Deep Researcher Loop       │    │
│  │ Thompson sampling │    │ THINK→EXECUTE→REFLECT    │    │
│  │ Learn from hist  │    │ Zero-cost monitoring      │    │
│  └──────────────────┘    └───────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│              STATE LAYER (InfiAgent)                        │
│  • File-based persistent state                               │
│  • Bounded context (~5K chars)                              │
│  • Workspace snapshots                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🖥️ User Interface (CLI)

AgentOS features an **interactive shell UI** with beautiful ASCII art and Rich-powered interface:

### Opening the UI

Simply run `agentos` without arguments to launch the interactive shell:

```bash
# Launch interactive shell (default)
agentos

# Show banner only (no shell)
agentos --no-shell

# Or use subcommands directly
agentos run "Create a web scraper"
agentos config show
agentos sessions
```

### Interactive Shell Features

| Feature | Description |
|---------|-------------|
| **ASCII Banner** | Pyfiglet-powered logo on launch |
| **Welcome Panel** | Feature highlights on startup |
| **Status Bar** | Model, Safety, Budget, Session info |
| **7-Step Pipeline** | Real-time execution visualization |
| **Rich Tables** | Colored configuration & skills tables |
| **Rich Panels** | Info/Error/Warning boxes |
| **Task Counter** | Track tasks executed |

### Shell UI Preview

**1. Launch & Welcome:**
```
    ___                    __  ____  _____
   /   | ____ ____  ____  / /_/ __ \/ ___/
  / /| |/ __ `/ _ \/ __ \/ __/ / / /\__ \
 / ___ / /_/ /  __/ / / / /_/ /_/ /___/ /
/_/  |_\__, /\___/_/ /_/\__/\____//____/
      /____/

╭────────────── Welcome ───────────────╮
│ ✓ AgentOS Shell Ready!              │
│                                      │
│ Features:                            │
│   • Run tasks with LLM              │
│   • 93 built-in skills              │
│   • ROMA Planning                   │
│   • MOSAIC Safety                   │
│   • Session persistence              │
╰──────────────────────────────────────╯
```

**2. Task Execution:**
```
━━━ Task #1 ━━━
Create a Python web scraper

Pipeline:
  1. Context Loading
  2. ROMA Planning (Task Decomposition)
  3. HTAA Tool Grouping
  4. MOSAIC Safety Check
  5. ToolTree Execution
  6. REDEREF Reflection
  7. State Persistence

⏳ Executing...
  [1] Loading 93 built-in skills...
  [2] ROMA: Decomposing task into subtasks...
  [4] MOSAIC: Verifying action safety...
  ✓ Safety check passed
  ✓ Task execution completed!
```

**3. Status Bar:**
```
╭───────────────── Status ──────────────────╮
│ Model: minimax-m2.5-free                  │
│ Safety: 🛡️ Enabled                        │
│ Budget: $1.00                             │
│ Max Steps: 100                            │
│ Session: main                             │
│ Tasks Run: 1                              │
╰───────────────────────────────────────────╯
```

### Available Commands in Shell

| Command | Shortcut | Description |
|---------|----------|-------------|
| `run <task>` | `r` | Execute a task |
| `sessions` | `s` | List/manage sessions |
| `config` | `c` | Show configuration |
| `skills` | `k` | List available skills |
| `info` | `i` | System information |
| `status` | - | Show current status |
| `clear` | - | Clear screen |
| `help` | `h` | Show help |
| `quit` | `q` | Exit AgentOS |

### Examples

```bash
# Launch shell
agentos

# In shell, type commands:
agentos> run Create a REST API with Flask
agentos> sessions --list
agentos> config --set budget 5.0
agentos> help
agentos> quit

# Or use directly without shell
agentos run "Build a web scraper" --budget 2.0
agentos config show
agentos sessions
```

## 🚀 Quick Start

### Prerequisites

| OS | Requirements |
|---|---------------|
| **macOS** | Python 3.10+, Terminal |
| **Linux** | Python 3.10+, Terminal |
| **Windows** | Python 3.10+, Command Prompt / PowerShell |

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/fikriaf/agentos.git
cd agentos
```

#### 2. Install Python Dependencies

```bash
# Option A: Using uv (recommended - faster)
pip install uv
uv pip install -e . --system

# Option B: Using pip
pip install -e .
```

#### 3. Configure API Key

```bash
# Set API key (required for LLM)
agentos config api_key YOUR_API_KEY

# Or use environment variable
# macOS / Linux:
export OPENCODE_ZEN_API_KEY=your_key_here

# Windows (Command Prompt):
set OPENCODE_ZEN_API_KEY=your_key_here

# Windows (PowerShell):
$env:OPENCODE_ZEN_API_KEY="your_key_here"
```

#### 4. Verify Installation

```bash
agentos info
```

---

### Platform-Specific Notes

#### macOS

```bash
# Using Homebrew Python
brew install python3
python3 -m pip install -e .

# Or using uv
brew install uv
uv pip install -e . --system
```

#### Linux (Ubuntu/Debian)

```bash
# Install Python
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Or install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv pip install -e . --system
```

#### Linux (Arch)

```bash
sudo pacman -S python python-pip
pip install -e .
```

#### Windows

```bash
# Using Python from python.org
# Download from https://www.python.org/downloads/

# Install using pip
pip install -e .

# Or using uv (PowerShell)
pip install uv
uv pip install -e . --system
```

#### WSL (Windows Subsystem for Linux)

```bash
# Install WSL first
wsl --install

# Then follow Linux instructions above
cd /mnt/d/script/OS/agentos
pip install -e .
```

---

### Configuration

### Basic Usage

```bash
# Run a task
agentos run "Create a Flask API with GET and POST endpoints"

# With options
agentos run "Build a web scraper" --budget 0.50 --max-steps 10

# Resume a previous session
agentos resume --session session_20260429_120000_abc123

# Interactive wizard mode
agentos wizard
```

## 📚 Research Foundation

AgentOS is built on 9 peer-reviewed papers from 2026:

| Paper | Concept | Key Innovation |
|-------|---------|---------------|
| **InfiAgent** | Infinite-Horizon Framework | File-based state externalization, bounded context |
| **ROMA** | Recursive Open Meta-Agent | Task decomposition into parallel subtask trees |
| **HTAA** | Hybrid Toolset Agentization | Tool grouping to reduce action space |
| **ToolTree** | MCTS Tool Planning | Dual-feedback Monte Carlo planning |
| **MOSAIC** | Safety Framework | Plan→Check→Act/Refuse with explicit refusal |
| **REDEREF** | Multi-Agent Routing | Thompson sampling for belief-guided delegation |
| **INTENT** | Budget-Aware Planning | Cost estimation and constraint satisfaction |
| **Deep Researcher** | Autonomous Loop | THINK→EXECUTE→REFLECT with zero-cost monitoring |
| **Context Engineering** | Multi-Layer CE | Context→Intent→Specification pyramid |

### Key Papers

1. **InfiAgent** — [arXiv:2601.03204](https://arxiv.org/abs/2601.03204)  
   *Infinite-Horizon Framework for General-Purpose Autonomous Agents*

2. **ROMA** — [arXiv:2602.01848](https://arxiv.org/abs/2602.01848)  
   *Recursive Open Meta-Agent Framework for Long-Horizon Multi-Agent Systems*

3. **HTAA** — [arXiv:2604.10917](https://arxiv.org/abs/2604.10917)  
   *Enhancing LLM Planning via Hybrid Toolset Agentization & Adaptation*

4. **ToolTree** — [arXiv:2603.12740](https://arxiv.org/abs/2603.12740)  
   *Efficient LLM Agent Tool Planning via Dual-Feedback MCTS*

5. **MOSAIC** — [arXiv:2603.03205](https://arxiv.org/abs/2603.03205)  
   *Modular Open Security Agent Integration Concept*

6. **REDEREF** — [arXiv:2603.13256](https://arxiv.org/abs/2603.13256)  
   *Training-Free Agentic AI: Probabilistic Control in Multi-Agent Systems*

7. **INTENT** — [arXiv:2602.11541](https://arxiv.org/abs/2602.11541)  
   *Budget-Constrained Planning for Tool Use*

8. **Deep Researcher** — [arXiv:2604.05854](https://arxiv.org/abs/2604.05854)  
   *Autonomous Framework for Deep Learning Experimentation*

9. **Context Engineering** — [arXiv:2603.09619](https://arxiv.org/abs/2603.09619)  
   *From Prompts to Corporate Multi-Agent Architecture*

## ⚙️ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **ROMA Planner** | Recursive task decomposition with parallel execution |
| **HTAA Executor** | Tool grouping reduces cognitive load |
| **ToolTree** | MCTS-based tool planning with lookahead |
| **MOSAIC Safety** | Explicit safety reasoning and refusal |
| **REDEREF Router** | Intelligent routing with Thompson sampling |
| **INTENT Budget** | Cost-aware planning and execution |
| **InfiAgent State** | File-based persistent memory |
| **Deep Researcher Loop** | THINK→EXECUTE→REFLECT pattern |

### Built-in Skills

AgentOS comes with **93 built-in skills** across 26 categories:

```
├── autonomous-ai-agents (4)
│   ├── agentos, claude-code, codex, opencode
├── creative (16)
│   ├── ascii-art, excalidraw, p5js, songwriting
├── devops (4)
│   ├── webhook-subscriptions, supabase
├── github (6)
│   ├── code-review, pr-workflow, repo-management
├── mlops (20)
│   ├── huggingface, vllm, llama-cpp, unsloth
├── software-development (22)
│   ├── tdd, debugging, security, ci-cd
└── ... 19 more categories
```

### CLI Commands

```bash
# Task execution
agentos run "your task here"           # Run a task
agentos run -s session_id              # Resume session
agentos run -n 10 -b 1.0               # With options

# Configuration
agentos config show                    # View config
agentos config set max_steps 100        # Set value
agentos config api_key YOUR_KEY        # Set API key
agentos config reset                   # Reset defaults

# Session management
agentos sessions                       # List all sessions
agentos resume -s session_id           # Resume session
agentos delete -s session_id           # Delete session

# Utilities
agentos info                           # System info
agentos wizard                         # Interactive mode
```

## 🔬 Technical Details

### Agent Pipeline

```
User Task
    │
    ▼
┌─────────────┐
│  Context    │ ← Load 93 built-in skills
│  Loading    │
└─────────────┘
    │
    ▼
┌─────────────┐     ┌─────────────┐
│  ROMA       │────▶│  INTENT     │
│  Planner    │     │  Budget     │
└─────────────┘     └─────────────┘
    │
    ▼
┌─────────────┐     ┌─────────────┐
│  ToolTree   │────▶│  HTAA       │
│  Planner    │     │  Executor   │
└─────────────┘     └─────────────┘
    │
    ▼
┌─────────────┐
│  MOSAIC     │ ← Safety check
│  Safety     │
└─────────────┘
    │
    ▼
┌─────────────┐
│  Execution  │ ← Run with registered tools
│             │
└─────────────┘
    │
    ▼
┌─────────────┐     ┌─────────────┐
│  REDEREF    │────▶│  Reflection │
│  Router     │     │  (Deep      │
│             │     │  Researcher)│
└─────────────┘     └─────────────┘
    │
    ▼
┌─────────────┐
│  InfiAgent  │ ← Persist state
│  State      │
└─────────────┘
    │
    ▼
   OUTPUT
```

### Supported LLM Providers

| Provider | Model | Base URL |
|----------|-------|----------|
| OpenCode Zen | minimax-m2.5-free | https://opencode.ai/zen/v1 |
| OpenRouter | Any | https://openrouter.ai/api/v1 |
| Custom | Any OpenAI-compatible | Configurable |

## 📖 Examples

### Example 1: Web Research

```bash
agentos run "Research the latest developments in quantum computing and create a summary report"
```

### Example 2: Code Generation

```bash
agentos run "Create a REST API for a todo list using Flask with SQLite database"
```

### Example 3: Data Analysis

```bash
agentos run "Analyze sales data from /data/sales.csv and generate visualization charts"
```

### Example 4: Resume Previous Task

```bash
# List sessions
agentos sessions

# Resume specific session
agentos resume -s session_20260429_120000_abc123 -t "Continue from where we left off"
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=agentos --cov-report=html

# Test specific module
pytest tests/test_planner.py -v
```

## 📦 Dependencies

```
core:
  - python >= 3.10
  - click >= 8.0
  - rich >= 13.0
  - httpx >= 0.25
  - tenacity >= 8.0

optional:
  - chromadb (vector memory)
  - redis (distributed memory)
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

AgentOS is built upon the pioneering research of:

- **InfiAgent** — State externalization for long-horizon agents
- **ROMA** — Recursive Open Meta-Agent framework
- **HTAA** — Hybrid Toolset Agentization
- **ToolTree** — MCTS-based tool planning
- **MOSAIC** — Modular Open Security Agent Integration
- **REDEREF** — Probabilistic control in multi-agent systems
- **INTENT** — Budget-aware planning
- **Deep Researcher** — Autonomous experimentation
- **Context Engineering** — Multi-layer agent architecture

## 📞 Contact

- GitHub Issues: [github.com/fikriaf/agentos/issues](https://github.com/fikriaf/agentos/issues)
- Discussions: [github.com/fikriaf/agentos/discussions](https://github.com/fikriaf/agentos/discussions)

---

<p align="center">
  <strong>Built with ❤️ on cutting-edge AI research</strong>
</p>
