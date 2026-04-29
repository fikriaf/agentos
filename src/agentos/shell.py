"""
AgentOS Interactive Shell - Full CLI UI/UX

A beautiful, interactive command-line interface for AgentOS with:
- Status bar showing system info
- Interactive input prompt
- Command history
- Real-time indicators
- Session management
"""

import sys
import os
import shlex
from typing import Optional, Dict, Any, List

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.box import ROUNDED
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import pyfiglet
    FIGLET_AVAILABLE = True
except ImportError:
    FIGLET_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


class AgentOSShell:
    """Interactive shell UI for AgentOS."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.running = True
        self.history: List[str] = []
        self.current_session: Optional[str] = None
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "model": "minimax-m2.5-free",
            "base_url": "https://opencode.ai/zen/v1",
            "max_steps": 100,
            "budget": 1.0,
            "safety_enabled": True,
            "auto_confirm": False,
        }
    
    def _render_banner(self) -> str:
        if FIGLET_AVAILABLE:
            try:
                figlet = pyfiglet.Figlet(font="slant", width=120)
                return f"[cyan]{figlet.renderText('AgentOS')}[/cyan]"
            except:
                pass
        return "[cyan]AgentOS[/cyan]"
    
    def _render_status_bar(self) -> Panel:
        if not RICH_AVAILABLE:
            return None
        status = f"""[bold cyan]Model:[/bold cyan] {self.config.get('model', 'unknown')[:20]}
[bold cyan]Safety:[/bold cyan] 🛡️ {'Enabled' if self.config.get('safety_enabled') else 'Disabled'}
[bold cyan]Budget:[/bold cyan] ${self.config.get('budget', 0):.2f}
[bold cyan]Session:[/bold cyan] {self.current_session or 'None'}"""
        return Panel(status.strip(), title="[bold]Status[/bold]", border_style="cyan", box=ROUNDED, width=40)
    
    def _process_command(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return True
        self.history.append(line)
        
        cmd = line.split()[0].lower() if line.split() else ""
        args = line.split()[1:] if len(line.split()) > 1 else []
        
        if cmd in ("quit", "exit", "q"):
            return False
        elif cmd in ("help", "h", "?"):
            self._show_help()
        elif cmd in ("clear", "cls"):
            console.clear() if RICH_AVAILABLE else os.system("clear")
        elif cmd in ("run", "r"):
            self._run_task(" ".join(args) if args else "")
        elif cmd in ("sessions", "s"):
            self._show_sessions()
        elif cmd in ("config", "c"):
            self._show_config()
        elif cmd in ("skills", "k"):
            self._show_skills()
        elif cmd in ("info", "i"):
            self._show_info()
        elif cmd in ("status"):
            self._show_status()
        else:
            self._run_task(line)
        return True
    
    def _show_help(self):
        text = """[bold cyan]AgentOS Shell - Help[/bold cyan]
[yellow]run <task>[/yellow] Execute task
[yellow]sessions[/yellow] List sessions
[yellow]config[/yellow] Show config
[yellow]skills[/yellow] List skills
[yellow]info[/yellow] System info
[yellow]status[/yellow] Show status
[yellow]help[/yellow] Show help
[yellow]quit[/yellow] Exit"""
        if RICH_AVAILABLE:
            console.print(Panel(text, border_style="cyan", box=ROUNDED))
    
    def _show_status(self):
        if RICH_AVAILABLE:
            console.print(self._render_status_bar())
    
    def _show_info(self):
        if RICH_AVAILABLE:
            t = Table(title="System Info", box=ROUNDED)
            t.add_column("Property", style="cyan")
            t.add_column("Value", style="white")
            t.add_row("Version", "0.1.0")
            t.add_row("Python", sys.version.split()[0])
            t.add_row("Rich", "✓" if RICH_AVAILABLE else "✗")
            t.add_row("PyFiglet", "✓" if FIGLET_AVAILABLE else "✗")
            console.print(t)
    
    def _show_config(self):
        if RICH_AVAILABLE:
            t = Table(title="Configuration", box=ROUNDED)
            t.add_column("Setting", style="cyan")
            t.add_column("Value", style="white")
            for k, v in self.config.items():
                t.add_row(str(k), str(v))
            console.print(t)
    
    def _show_sessions(self):
        if RICH_AVAILABLE:
            console.print(Panel("[yellow]No sessions[/yellow]", border_style="yellow"))
    
    def _show_skills(self):
        if RICH_AVAILABLE:
            t = Table(title="Built-in Skills (93)", box=ROUNDED)
            t.add_column("#", style="dim", width=4)
            t.add_column("Category", style="cyan")
            t.add_column("Skills", style="white")
            cats = [
                ("autonomous-ai-agents", "agentos, claude-code, codex, opencode"),
                ("creative", "ascii-art, excalidraw, p5js, songwriting"),
                ("devops", "webhook-subscriptions, supabase"),
                ("github", "code-review, pr-workflow, repo-management"),
                ("mlops", "huggingface, vllm, llama-cpp, unsloth"),
                ("software-development", "tdd, debugging, security, ci-cd"),
                ("data-science", "jupyter, pandas, visualization"),
                ("browser", "browser-harness, dogfood"),
            ]
            for i, (c, s) in enumerate(cats, 1):
                t.add_row(str(i), c, s)
            console.print(t)
    
    def _run_task(self, task: str):
        if not task:
            if RICH_AVAILABLE:
                console.print(Panel("[yellow]Provide task:[/yellow] run <task>", border_style="yellow"))
            return
        if RICH_AVAILABLE:
            console.print(Panel(f"[cyan]Task:[/cyan] {task}\n\n[dim]Run: agentos run \"{task}\"[/dim]", border_style="green"))
        else:
            print(f"Task: {task}")
    
    def run(self):
        if RICH_AVAILABLE and console:
            console.clear()
            # Banner already shown by CLI, show welcome only
            welcome = """[bold green]✓[/bold green] AgentOS Shell Ready!
[cyan]Features:[/cyan]
  • Run tasks with natural language
  • 93 built-in skills
  • Session management
  • Safety with MOSAIC
[yellow]Type 'help' for commands[/yellow]"""
            console.print(Panel(welcome, border_style="green", box=ROUNDED))
        else:
            print("AgentOS Shell - Type 'help'")
        
        while self.running:
            try:
                prompt = f"[bold cyan]agentos:{self.current_session or 'main'}> [/bold cyan]"
                line = console.input(prompt) if RICH_AVAILABLE else input("agentos> ")
                self.running = self._process_command(line)
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
                continue
            except EOFError:
                break
        
        if RICH_AVAILABLE:
            console.print(Panel("[cyan]Goodbye! 👋[/cyan]", border_style="cyan"))


def run_shell():
    """Entry point."""
    shell = AgentOSShell()
    shell.run()


if __name__ == "__main__":
    run_shell()