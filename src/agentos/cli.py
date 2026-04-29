"""AgentOS CLI - Main entry point with Enhanced UI."""

import asyncio
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.box import ROUNDED, DOUBLE

from agentos import __version__
from agentos.config import get_config, save_config, AgentOSConfig
from agentos.llm.client import LLMClient, LLMConfig
from agentos.llm.prompts import SYSTEM_PROMPT
from agentos.skills import get_skills_manager
from agentos.agents.planner import PlannerAgent
from agentos.agents.executor import ToolExecutor
from agentos.agents.safety import SafetyChecker
from agentos.agents.reflection import ReflectionAgent
from agentos.memory.session import SessionManager
from agentos.tools.shell import ShellTool
from agentos.tools.http import HTTPClient
from agentos.models.task import TaskPlan, Action
from agentos.models.tool import ToolRegistry
from agentos.utils.logger import get_logger
from agentos.utils.budget import BudgetTracker
from agentos.ui import (
    AgentOSBanner, AgentOSPanels, AgentOSTables, AgentOSMenu,
    print_banner, print_success, print_error, print_warning, print_table
)

console = Console()
logger = get_logger("agentos.cli")


def get_api_key() -> str:
    """Get API key from env or config."""
    return os.environ.get("OPENCODE_ZEN_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or ""


@click.group()
@click.version_option(version=__version__)
def cli():
    """AgentOS - Autonomous Agent CLI Framework with Built-in Safety."""
    # Print welcome banner
    print_banner("AgentOS")
    console.print("")
    console.print("[dim]  Autonomous Agent Framework with Built-in Safety[/dim]")
    console.print("[dim]  Version {}[/dim]".format(__version__))
    console.print("")


# =============================================================================
# CONFIG COMMAND
# =============================================================================
@cli.group("config")
def config_cmd():
    """Manage AgentOS configuration."""
    pass


@config_cmd.command("show")
def config_show():
    """Show current configuration."""
    config = get_config()

    table = Table(title="AgentOS Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Model", config.model)
    table.add_row("Base URL", config.base_url)
    table.add_row("Max Tokens", str(config.max_tokens))
    table.add_row("Temperature", str(config.temperature))
    table.add_row("Max Steps", str(config.max_steps))
    table.add_row("Default Budget", f"${config.default_budget}")
    table.add_row("Auto Confirm", str(config.auto_confirm))
    table.add_row("Safety Enabled", str(config.safety_enabled))
    table.add_row("Block Dangerous", str(config.block_dangerous))
    table.add_row("Workspace", config.workspace_dir)
    table.add_row("Memory Dir", config.memory_persist_dir)

    # Show API key status
    api_key = get_api_key()
    if api_key:
        table.add_row("API Key", f"{api_key[:10]}...{api_key[-4:]}")
    else:
        table.add_row("API Key", "[red]Not set[/red]")

    console.print(table)
    console.print(f"\n[dim]Config file: {config.config_file}[/dim]")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set configuration value."""
    config = get_config()

    # Valid keys
    valid_keys = {
        "model": str,
        "base_url": str,
        "max_tokens": int,
        "temperature": float,
        "max_steps": int,
        "default_budget": float,
        "auto_confirm": bool,
        "safety_enabled": bool,
        "block_dangerous": bool,
        "workspace_dir": str,
        "memory_persist_dir": str,
    }

    if key not in valid_keys:
        console.print(f"[red]Invalid key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(valid_keys.keys())}")
        return

    # Convert value
    try:
        converted = valid_keys[key](value)
    except ValueError:
        console.print(f"[red]Invalid value for {key}: {value}[/red]")
        return

    setattr(config, key, converted)
    save_config(config)
    console.print(f"[green]Set {key} = {converted}[/green]")


@config_cmd.command("api_key")
@click.argument("api_key", required=False)
@click.option("--env", is_flag=True, help="Save to environment variable")
def config_api_key(api_key: Optional[str], env: bool):
    """Set API key."""
    if env:
        console.print("[yellow]To persist API key, add to your shell profile:[/yellow]")
        console.print("  export OPENCODE_ZEN_API_KEY=your_key")
        return

    if not api_key:
        api_key = Prompt.ask("Enter API key", password=True)

    if api_key:
        config = get_config()
        config.api_key = api_key
        save_config(config)
        console.print("[green]API key saved to config[/green]")
        console.print("[dim]Tip: Also add to shell profile for persistence:[/dim]")
        console.print(f"  export OPENCODE_ZEN_API_KEY={api_key[:10]}...")
    else:
        console.print("[red]No API key provided[/red]")


@config_cmd.command("reset")
def config_reset():
    """Reset configuration to defaults."""
    if not Confirm.ask("Reset all configuration to defaults?"):
        return

    default_config = AgentOSConfig()
    save_config(default_config)
    console.print("[green]Configuration reset to defaults[/green]")


# =============================================================================
# RUN COMMAND
# =============================================================================
@cli.command()
@click.argument("task", required=False)
@click.option("--session", "-s", help="Session ID to resume")
@click.option("--budget", "-b", type=float, help="Budget limit (USD)")
@click.option("--max-steps", "-n", type=int, help="Max steps")
@click.option("--model", "-m", help="Model to use")
@click.option("--auto-confirm", "-y", is_flag=True, help="Skip confirmations")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(
    task: Optional[str],
    session: Optional[str],
    budget: Optional[float],
    max_steps: Optional[int],
    model: Optional[str],
    auto_confirm: bool,
    verbose: bool,
):
    """Run AgentOS with a task."""
    if verbose:
        import logging
        logger.setLevel(logging.DEBUG)

    asyncio.run(_run_async(
        task=task,
        session_id=session,
        budget=budget,
        max_steps=max_steps,
        model=model,
        auto_confirm=auto_confirm,
    ))


async def _run_async(
    task: Optional[str],
    session_id: Optional[str],
    budget: Optional[float],
    max_steps: Optional[int],
    model: Optional[str],
    auto_confirm: bool,
):
    """Async run implementation."""
    # Load config
    config = get_config()

    # Check API key
    api_key = get_api_key() or config.api_key
    if not api_key:
        console.print("[red]Error: No API key found[/red]")
        console.print("Set it with: agentos config api_key YOUR_KEY")
        console.print("Or: export OPENCODE_ZEN_API_KEY=your_key")
        return

    # Get task from user if not provided
    if not task:
        task = Prompt.ask("[bold blue]What would you like me to help with?[/bold blue]")

    console.print(Panel(f"[bold cyan]AgentOS[/bold cyan] - {task}"))

    # Load skills and build system prompt
    skills_mgr = get_skills_manager()
    skills_context = skills_mgr.get_skills_context(task)
    system_prompt = SYSTEM_PROMPT.replace("{skills_context}", skills_context)
    
    # Initialize LLM with skills context
    llm_config = LLMConfig(
        model=model or config.model,
        api_key=api_key,
        base_url=config.base_url,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        system_prompt=system_prompt,
    )
    llm = LLMClient(llm_config)
    console.print(f"[dim]Loaded {skills_mgr.get_total_count()} built-in skills[/dim]")

    # Set budget
    budget = budget or config.default_budget
    llm.set_budget(budget)

    # Initialize components
    budget_tracker = BudgetTracker()
    session_manager = SessionManager()

    # Create or resume session
    if session_id:
        current_session = session_manager.load_session(session_id)
        if not current_session:
            console.print(f"[yellow]Session {session_id} not found, creating new[/yellow]")
            current_session = session_manager.create_session(task, session_id)
    else:
        current_session = session_manager.create_session(task)
        # Save session immediately so it persists
        from agentos.models.memory import AgentState
        initial_state = AgentState(session_id=current_session.session_id, task=task)
        session_manager.save_session(current_session, initial_state)

    console.print(f"[dim]Session: {current_session.session_id}[/dim]")

    # Initialize agents with skills context
    skills_context = skills_mgr.get_skills_context(task)
    planner = PlannerAgent(llm, budget_tracker, skills_context=skills_context)
    executor = ToolExecutor(llm, skills_context=skills_context)
    safety = SafetyChecker(llm)
    reflection = ReflectionAgent(llm, skills_context=skills_context)

    # Register default tools
    tools = {
        "bash": ShellTool(),
        "http": HTTPClient(),
    }
    for name, tool in tools.items():
        executor.register_tool(tool)

    # Get effective max_steps
    effective_max_steps = max_steps or config.max_steps
    effective_auto_confirm = auto_confirm or config.auto_confirm

    # Planning phase
    console.print("\n[bold yellow]Planning...[/bold yellow]")
    try:
        plan = await planner.decompose(task)
        console.print(f"[dim]Created {len(plan.subtasks)} subtasks[/dim]")
        console.print(f"[dim]Parallel groups: {plan.parallel_groups}[/dim]")
        console.print(f"[dim]Estimated cost: ${plan.estimated_total_cost:.4f}[/dim]")
    except Exception as e:
        console.print(f"[red]Planning failed: {e}[/red]")
        return

    # Execution loop
    console.print("\n[bold yellow]Executing...[/bold yellow]")
    step = 0
    results = []

    for subtask in plan.subtasks:
        step += 1
        if step > effective_max_steps:
            console.print(f"[yellow]Max steps ({effective_max_steps}) reached[/yellow]")
            break

        console.print(f"\n[bold]Step {step}:[/bold] {subtask.description[:60]}...")

        # Safety check
        action = Action(
            tool_name="bash",
            args={"command": subtask.description},
            task_id=subtask.id
        )
        safety_result = await safety.check(action)

        if safety_result.decision == "refuse":
            console.print(f"[red]✗ Refused: {safety_result.reason}[/red]")
            plan.mark_failed(subtask.id, safety_result.reason)
            continue

        if safety_result.decision == "verify" and not effective_auto_confirm:
            console.print(f"[yellow]⚠ Verification required: {safety_result.reason}[/yellow]")
            if not Confirm.ask("Proceed anyway?"):
                plan.mark_failed(subtask.id, "User refused")
                continue

        # Execute
        result = await executor._execute_subtask(subtask, tools)
        results.append(result)

        if result.success:
            console.print(f"[green]✓[/green] {result.output[:100] if result.output else 'Done'}...")
        else:
            console.print(f"[red]✗[/red] {result.error}")

        # Check budget
        cost = llm.get_cost_summary()
        if cost.get("total_cost", 0) >= budget:
            console.print(f"[yellow]Budget limit reached: ${cost.get('total_cost', 0):.4f}[/yellow]")
            break

    # Reflection
    console.print("\n[bold yellow]Reflecting...[/bold yellow]")
    reflection_result = await reflection.reflect(task, results, plan)

    console.print(f"[dim]Decision: {reflection_result.decision}[/dim]")
    if reflection_result.lessons_learned:
        console.print(f"[dim]Lessons: {reflection_result.lessons_learned}[/dim]")

    # Summary
    console.print("\n[bold green]Summary[/bold green]")
    console.print(f"Steps: {len(results)}")
    console.print(f"Successful: {sum(1 for r in results if r.success)}")
    console.print(f"Failed: {sum(1 for r in results if not r.success)}")
    console.print(f"Total cost: ${llm.get_cost_summary().get('total_cost', 0):.4f}")
    console.print(f"Session: {current_session.session_id}")

    console.print("\n[bold cyan]Use 'agentos resume --session {id}' to continue later[/bold cyan]")


# =============================================================================
# SESSION COMMANDS
# =============================================================================
@cli.command("sessions")
def sessions_cmd():
    """List all sessions."""
    session_manager = SessionManager()
    all_sessions = session_manager.list_sessions()

    if not all_sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return

    table = Table(title="AgentOS Sessions")
    table.add_column("Session ID")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Cost")
    table.add_column("Updated")

    for s in all_sessions:
        task_short = s.task[:40] + "..." if len(s.task) > 40 else s.task
        table.add_row(
            s.session_id,
            task_short,
            s.status,
            f"${s.total_cost:.4f}",
            s.updated_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@cli.command()
@click.option("--session", "-s", required=True, help="Session ID to resume")
@click.option("--task", "-t", help="Additional task context")
def resume(session: str, task: Optional[str]):
    """Resume a previous session."""
    asyncio.run(_resume_async(session, task))


async def _resume_async(session_id: str, task: Optional[str]):
    """Async resume implementation."""
    session_manager = SessionManager()
    current_session = session_manager.load_session(session_id)

    if not current_session:
        console.print(f"[red]Session {session_id} not found[/red]")
        return

    console.print(f"[green]Resuming session: {current_session.task}[/green]")

    # Append task if provided
    if task:
        new_task = f"{current_session.task}\n\nAdditional: {task}"
    else:
        new_task = current_session.task

    await _run_async(
        task=new_task,
        session_id=session_id,
        budget=None,
        max_steps=None,
        model=None,
        auto_confirm=False,
    )


@cli.command()
@click.option("--session", "-s", required=True, help="Session ID to delete")
def delete(session: str):
    """Delete a session."""
    if not Confirm.ask(f"Delete session {session}?"):
        return

    session_manager = SessionManager()
    if session_manager.delete_session(session):
        console.print(f"[green]Session {session} deleted[/green]")
    else:
        console.print(f"[red]Failed to delete session {session}[/red]")


# =============================================================================
# WIZARD MODE
# =============================================================================
@cli.command()
def wizard():
    """Start interactive wizard mode."""
    console.print(Panel.fit(
        "[bold cyan]AgentOS Wizard Mode[/bold cyan]\n\n"
        "I'll help you set up a task step by step."
    ))

    # Step 1: What do you want to do?
    task_type = Prompt.ask(
        "[bold]What would you like to do?[/bold]",
        choices=["research", "code", "analyze", "automate", "other"],
        default="code",
    )

    # Step 2: Task description
    task = Prompt.ask("[bold]Describe your task:[/bold]")

    # Step 3: Budget
    budget_str = Prompt.ask("[bold]Budget limit (USD):[/bold]", default="1.0")
    try:
        budget = float(budget_str)
    except ValueError:
        budget = 1.0

    # Summary
    console.print("\n[bold green]Summary:[/bold green]")
    console.print(f"Task type: {task_type}")
    console.print(f"Task: {task}")
    console.print(f"Budget: ${budget}")

    if Confirm.ask("\n[bold]Start execution?[/bold]"):
        asyncio.run(_run_async(
            task=task,
            session_id=None,
            budget=budget,
            max_steps=None,
            model=None,
            auto_confirm=False,
        ))


# =============================================================================
# INFO COMMAND
# =============================================================================
@cli.command()
def info():
    """Show AgentOS information."""
    config = get_config()
    api_key = "✓" if get_api_key() or config.api_key else "✗"

    console.print(Panel(
        f"""[bold]AgentOS[/bold] v{__version__}

[bold cyan]Status:[/bold cyan]
- API Key: {api_key}
- Python: ✓

[bold cyan]Configuration:[/bold cyan]
- Model: {config.model}
- Base URL: {config.base_url}
- Max Steps: {config.max_steps}
- Budget: ${config.default_budget}

[bold cyan]Features:[/bold cyan]
- ROMA Task Decomposition
- HTAA Tool Grouping
- MOSAIC Safety
- INFIAgent Memory
- ChromaDB Vector Store
- REDEREF Reflection
- INTENT Budget Awareness

[bold cyan]Commands:[/bold cyan]
- agentos run "task"     Run a task
- agentos config show    Show config
- agentos config set     Set config
- agentos sessions       List sessions
- agentos wizard         Interactive mode""",
        title="AgentOS Info",
    ))


# =============================================================================
# MAIN
# =============================================================================
def main():
    cli()


if __name__ == "__main__":
    main()
