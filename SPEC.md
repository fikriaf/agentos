# SPEC.md — AgentOS CLI

## 1. Objective

**AgentOS** adalah autonomous agent CLI framework open-source yang menggabungkan semua paper AI/agent 2026 (InfiAgent, ROMA, HTAA, ToolTree, MOSAIC, REDEREF, INTENT, Deep Researcher, Context Engineering) jadi satu cohesive system.

### Vision
```
┌─────────────────────────────────────────────────────┐
│                    USER INPUT                        │
│            "Research climate ML, build model"         │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              CONTEXT ENGINEERING                      │
│  Load context → Align intent → Load safety policies  │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              PLANNING LAYER (ROMA + INTENT)          │
│  Task decomposition → Parallel planning → Budget     │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              EXECUTION LAYER (HTAA + ToolTree)       │
│  Tool grouping → MCTS planning → Execute             │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              SAFETY LAYER (MOSAIC)                   │
│  Plan → Check → Act/Refuse                          │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              MEMORY LAYER (InfiAgent + Vector DB)    │
│  File-based state → Embeddings → Semantic search     │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              REFLECTION LAYER (REDEREF)              │
│  Learn from history → Improve routing → Iterate      │
└─────────────────────────────────────────────────────┘
```

### User Stories

1. **Developer** ingin otomatisasi research workflow → ketik `agentos research "topik X"` → agent jalan sendiri
2. **Non-technical** mau analisis data → wizard mode → step-by-step guidance
3. **Power user** mau custom agent → scripting API → full control

### Success Criteria

- [ ] Agent bisa complete multi-step task (5+ steps) tanpa error
- [ ] Safety check mencegah dangerous operations
- [ ] Memory system bikin agent "ingat" konteks session sebelumnya
- [ ] Vector DB enable semantic search over conversation history
- [ ] Budget tracking limit API costs
- [ ] CLI usable oleh developer dan non-technical
- [ ] Extensible: bisa add custom tools, MCP servers

---

## 2. Tech Stack

### Core
- **Language:** Python 3.11+
- **CLI Framework:** Click + Rich (TUI)
- **Async:** AsyncIO + httpx
- **LLM:** OpenRouter SDK (Claude, GPT, Gemini, DeepSeek, dll)

### Memory
- **Vector DB:** Qdrant (lightweight, embedded mode) atau ChromaDB
- **State:** File-based (workspace snapshots)
- **Cache:** Redis (optional)

### Tools
- **MCP Client:** FastMCP atau MCP Python SDK
- **Shell:** asyncio.subprocess
- **Web:** httpx + BeautifulSoup

### Testing
- **Framework:** pytest
- **Mocking:** pytest-asyncio + unittest.mock

---

## 3. Commands

### CLI Entry Point
```bash
# Install
pip install agentos

# Run agent
agentos run "research tentang renewable energy trends"
agentos run "build simple todo app with React"

# Interactive mode
agentos shell

# Memory search
agentos memory search "apa yang kamu ingat tentang project sebelumnya"

# Agent config
agentos config set model claude-sonnet-4
agentos config set budget 10.00

# Tool management
agentos tools list
agentos tools add github
agentos tools remove web-search
```

### Internal Commands (for agent)
```bash
# Planning
agentos plan --task "build ecommerce" --budget 5.00

# Execution
agentos exec --tool bash --args "ls -la"
agentos exec --tool mcp_github --args "create_pr"

# Safety check
agentos check --action "delete /system" --context "user asked to clean up"

# Memory
agentos memory add --content "User prefers dark mode"
agentos memory query --embedding "user preferences"

# Monitor
agentos monitor --watch
```

---

## 4. Project Structure

```
agentos/
├── SPEC.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── src/
│   └── agentos/
│       ├── __init__.py
│       ├── cli.py                 # Click CLI entry point
│       ├── main.py                # Shell/Repl mode
│       ├── config.py              # Config management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── message.py         # Message/Chat models
│       │   ├── task.py            # Task decomposition
│       │   ├── tool.py            # Tool definitions
│       │   └── memory.py          # Memory/Session models
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py            # Base agent class
│       │   ├── planner.py          # ROMA + INTENT planner
│       │   ├── executor.py         # HTAA + ToolTree executor
│       │   ├── safety.py           # MOSAIC safety checker
│       │   └── reflection.py        # REDEREF reflection
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── file_state.py       # InfiAgent file-based state
│       │   ├── vector_store.py     # Qdrant/Chroma vector DB
│       │   └── session.py          # Session management
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py             # Base tool class
│       │   ├── shell.py            # Shell command tool
│       │   ├── http.py             # HTTP/web tool
│       │   └── mcp.py              # MCP client tool
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py           # OpenRouter client
│       │   ├── providers.py        # Multi-provider support
│       │   └── prompts.py          # System prompts
│       └── utils/
│           ├── __init__.py
│           ├── logger.py           # Logging
│           └── budget.py           # Budget tracker
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   │   ├── test_planner.py
│   │   ├── test_executor.py
│   │   └── test_safety.py
│   ├── test_memory/
│   │   ├── test_file_state.py
│   │   └── test_vector_store.py
│   └── test_tools/
│       ├── test_shell.py
│       └── test_mcp.py
├── examples/
│   ├── research_agent.py
│   ├── coding_agent.py
│   └── data_analysis.py
└── docs/
    ├── installation.md
    ├── quickstart.md
    ├── tools.md
    └── api.md
```

---

## 5. Code Style

### Python Style Guide
- **Format:** Black + isort
- **Type Hints:** Full annotations (PEP 484)
- **Async:** Use async/await everywhere
- **Error Handling:** Custom exceptions + result types

### Example Code

```python
# src/agentos/agents/planner.py
from typing import Protocol, AsyncIterator
from dataclasses import dataclass
import asyncio

@dataclass
class TaskPlan:
    """Represents a decomposed task plan from ROMA."""
    task_id: str
    subtasks: list[SubTask]
    estimated_cost: float
    parallel_groups: list[list[int]]  # Task indices that can run in parallel

@dataclass
class SubTask:
    """Atomic unit of work."""
    id: int
    description: str
    tools_needed: list[str]
    dependencies: set[int]
    estimated_duration: float

class PlannerAgent:
    """ROM A + INTENT based planner with budget awareness."""

    def __init__(
        self,
        llm_client: LLMClient,
        budget_tracker: BudgetTracker,
    ) -> None:
        self.llm = llm_client
        self.budget = budget_tracker

    async def decompose(
        self,
        task: str,
        max_parallel: int = 5,
    ) -> TaskPlan:
        """Decompose task using ROMA's recursive approach."""
        prompt = PLANNER_PROMPT.format(
            task=task,
            max_parallel=max_parallel,
        )

        response = await self.llm.complete(prompt)
        plan = self._parse_plan(response)

        # INTENT: Estimate and validate budget
        estimated = self.budget.estimate(plan)
        if estimated > self.budget.remaining:
            plan = await self._reduce_scope(plan, self.budget.remaining)

        return plan

    async def _reduce_scope(
        self,
        plan: TaskPlan,
        budget: float,
    ) -> TaskPlan:
        """ INTENT: Reduce plan scope to fit budget."""
        # Remove lowest-priority subtasks until within budget
        ...
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `SCREAMING_SNAKE_CASE`
- Private: `_prefixed_with_underscore`
- Async: `async_method_name`

---

## 6. Testing Strategy

### Test Levels

| Level | Coverage | Location | Framework |
|-------|----------|----------|-----------|
| Unit | Functions/Classes | `tests/` | pytest |
| Integration | Tool execution | `tests/test_tools/` | pytest + docker |
| E2E | Full agent loops | `tests/e2e/` | pytest + fixtures |

### Test Coverage Goals
- **Phase 1:** 70% coverage
- **Phase 2:** 85% coverage
- **Launch:** 90% coverage

### Key Test Cases

```python
# tests/test_agents/test_planner.py
class TestPlannerAgent:
    async def test_decompose_simple_task(self):
        """Planner should decompose task into subtasks."""
        planner = PlannerAgent(llm=mock_llm, budget=mock_budget)
        plan = await planner.decompose("build simple todo app")

        assert len(plan.subtasks) > 0
        assert plan.estimated_cost > 0

    async def test_budget_constraint(self):
        """Planner should reduce scope if over budget."""
        planner = PlannerAgent(llm=mock_llm, budget=Budget(remaining=0.01))
        plan = await planner.decompose("build full ecommerce platform")

        assert plan.estimated_cost <= 0.01

# tests/test_memory/test_vector_store.py
class TestVectorStore:
    async def test_semantic_search(self):
        """Should find semantically similar memories."""
        store = VectorStore(chroma_path="/tmp/test")
        await store.add("User prefers dark mode", metadata={"type": "preference"})
        await store.add("Dark mode saves battery", metadata={"type": "fact"})

        results = await store.search("what does user like?")
        assert "dark mode" in results[0].content.lower()
```

### CI/CD
- **Lint:** Ruff + MyPy
- **Format:** Black + isort
- **Test:** pytest + coverage
- **Publish:** GitHub Actions → PyPI

---

## 7. Boundaries

### Always Do
- [ ] Run tests before commit (`pytest`)
- [ ] Type check before PR (`mypy src/`)
- [ ] Lint before PR (`ruff check src/`)
- [ ] Document public APIs
- [ ] Handle errors gracefully with user-friendly messages
- [ ] Track budget for every LLM call
- [ ] Safety check before dangerous operations

### Ask First
- [ ] Add new LLM provider
- [ ] Change vector DB backend
- [ ] Modify safety policies
- [ ] Add new core module
- [ ] Breaking changes to CLI interface

### Never Do
- [ ] Commit secrets/API keys
- [ ] Block on user input without timeout
- [ ] Execute shell commands without sandbox
- [ ] Trust external tool output blindly
- [ ] Skip safety checks for "quick fixes"
- [ ] Make network calls without timeout
- [ ] Store sensitive data in vector DB

---

## 8. Key Implementation Details

### Safety Layer (MOSAIC)
```python
# Every action goes through safety check
class SafetyChecker:
    async def check(
        self,
        action: Action,
        context: dict,
    ) -> SafetyResult:
        """MOSAIC-style plan→check→act/refuse."""
        risk_factors = await self._assess_risk(action, context)

        if risk_factors.is_dangerous:
            return SafetyResult(
                decision="refuse",
                reason=risk_factors.reason,
                alternatives=risk_factors.suggestions,
            )

        if risk_factors.needs_verification:
            return SafetyResult(
                decision="verify",
                reason="Confirmation needed",
                verification_steps=risk_factors.steps,
            )

        return SafetyResult(decision="proceed")
```

### Memory System (InfiAgent + Vector DB)
```python
# File-based state for long-horizon tasks
class FileStateManager:
    """InfiAgent-style externalized state."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.snapshot_interval = 10  # steps

    async def save_snapshot(self, state: AgentState) -> None:
        """Save bounded snapshot to file."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "workspace_files": list(self.workspace.rglob("*")),
            "recent_actions": state.history[-10:],  # Bounded
            "current_plan": state.plan,
        }
        path = self.workspace / f"snapshot_{state.task_id}.json"
        path.write_text(json.dumps(snapshot, indent=2))

# Vector search for semantic memory
class VectorMemory:
    """ChromaDB-backed semantic memory."""

    async def search(self, query: str, k: int = 5) -> list[Memory]:
        embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )
        return [Memory(**r) for r in results]
```

### Tool Execution (HTAA + ToolTree)
```python
class ToolExecutor:
    """HTAA-style tool grouping + ToolTree MCTS planning."""

    async def plan_tools(
        self,
        subtask: SubTask,
        available_tools: list[Tool],
    ) -> list[ToolCall]:
        """Use MCTS to plan optimal tool sequence."""
        # Group tools (HTAA)
        tool_groups = self._group_tools(available_tools)

        # MCTS planning (ToolTree)
        tree = MCTSTree(root=ToolNode(subtask.description))

        for _ in range(self.max_iterations):
            tree.simulate(self._uct_score)

        return tree.get_best_sequence()

    async def execute(
        self,
        plan: list[ToolCall],
        parallel_groups: list[list[int]],
    ) -> list[Result]:
        """Execute tools respecting parallel groups."""
        results = []
        for group in parallel_groups:
            # Execute group in parallel
            group_results = await asyncio.gather(
                *[self._execute_call(plan[i]) for i in group]
            )
            results.extend(group_results)
        return results
```

---

## 9. Roadmap

### Phase 1: Core Framework
- [ ] Project setup (pyproject, structure)
- [ ] CLI framework (Click + Rich)
- [ ] LLM client (OpenRouter multi-provider)
- [ ] Basic agent loop (plan → exec → reflect)

### Phase 2: Advanced Features
- [ ] ROMA planner (task decomposition)
- [ ] HTAA tool grouping
- [ ] ToolTree MCTS planning
- [ ] MOSAIC safety layer
- [ ] INTENT budget tracking

### Phase 3: Memory System
- [ ] InfiAgent file-based state
- [ ] Vector DB integration (ChromaDB)
- [ ] Session management
- [ ] Semantic search

### Phase 4: Polish
- [ ] REDEREF reflection learning
- [ ] Non-technical wizard mode
- [ ] MCP server support
- [ ] Comprehensive tests
- [ ] Documentation

---

## 10. Decisions

1. **Vector DB:** ChromaDB (simple, embedded mode)
2. **Shell:** Full access (no sandbox)
3. **Persistence:** Local first, cloud sync later
4. **Pricing:** 100% free forever (open source)
5. **License:** MIT
