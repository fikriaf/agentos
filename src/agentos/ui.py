"""AgentOS Enhanced CLI UI Components.

Rich CLI components for AgentOS - provides beautiful terminal UI
with ASCII art banners, tables, panels, and interactive menus.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

# Rich components
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.layout import Layout
    from rich.tree import Tree
    from rich.prompt import Prompt, Confirm
    from rich.style import Style
    from rich.text import Text
    from rich.align import Align
    from rich.box import Box, ROUNDED, DOUBLE, DOUBLE_EDGE
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ASCII art tools
try:
    import pyfiglet
    FIGLET_AVAILABLE = True
except ImportError:
    FIGLET_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


# =============================================================================
# ASCII Art Banner Generator
# =============================================================================

@dataclass
class AgentOSBanner:
    """ASCII art banner for AgentOS branding."""
    
    @staticmethod
    def render(text: str = "AgentOS", font: str = "slant") -> str:
        """Render text as ASCII art banner."""
        if not FIGLET_AVAILABLE:
            return f"""
╔══════════════════════════════════╗
║          {text.upper():^20}          ║
║     Autonomous Agent Framework  ║
╚══════════════════════════════════╝
"""
        
        try:
            ascii_banner = pyfiglet.Figlet(font=font, width=120)
            result = ascii_banner.renderText(text)
            return result
        except Exception:
            return f"[ AgentOS ]"
    
    @staticmethod
    def render_small(text: str = "AgentOS") -> str:
        """Render small banner for inline display."""
        if not FIGLET_AVAILABLE:
            return f"[ {text} ]"
        
        try:
            ascii_banner = pyfiglet.Figlet(font="small", width=80)
            return ascii_banner.renderText(text)
        except Exception:
            return f"[ {text} ]"


# =============================================================================
# Rich Panel Components
# =============================================================================

class AgentOSPanels:
    """Rich panel templates for AgentOS CLI."""
    
    # Color scheme
    COLORS = {
        "primary": "cyan",
        "secondary": "blue", 
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "magenta",
        "muted": "dim",
    }
    
    @staticmethod
    def welcome() -> Optional[Panel]:
        """Welcome panel with logo."""
        if not RICH_AVAILABLE:
            return None
            
        banner = """
╔═══════════════════════════════════════════════════════════╗
║   ██████╗ ███████╗██╗      ██████╗  ██████╗ ██████╗   ║
║   ██╔══██╗██╔════╝██║     ██╔═══██╗██╔═══██╗██╔══██╗  ║
║   ██████╔╝█████╗   ██║     ██║   ██║██║   ██║██████╔╝  ║
║   ██╔══██╗██╔══╝   ██║     ██║   ██║██║   ██║██╔══██╗  ║
║   ██║  ██║███████╗███████╗╚██████╔╝╚██████╔╝██║  ██║  ║
║   ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝  ║
║                  Framework v1.0.0                     ║
╚═══════════════════════════════════════════════════════════╝
"""
        return Panel(
            banner,
            title="[bold cyan]Welcome to AgentOS[/bold cyan]",
            border_style="cyan",
            box=DOUBLE,
            padding=(1, 2),
        )
    
    @staticmethod
    def header(title: str, subtitle: str = "") -> Optional[Panel]:
        """Create header panel."""
        if not RICH_AVAILABLE:
            return None
        
        content = f"[bold]{title}[/bold]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        
        return Panel(
            content,
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 2),
        )
    
    @staticmethod
    def success(message: str) -> Optional[Panel]:
        """Success panel (green)."""
        if not RICH_AVAILABLE:
            return None
        return Panel(
            f"✓ {message}",
            border_style="green",
            box=ROUNDED,
            style="on green",
        )
    
    @staticmethod
    def error(message: str) -> Optional[Panel]:
        """Error panel (red)."""
        if not RICH_AVAILABLE:
            return None
        return Panel(
            f"✗ {message}",
            border_style="red",
            box=ROUNDED,
            style="on red",
        )
    
    @staticmethod
    def warning(message: str) -> Optional[Panel]:
        """Warning panel (yellow)."""
        if not RICH_AVAILABLE:
            return None
        return Panel(
            f"⚠ {message}",
            border_style="yellow",
            box=ROUNDED,
        )
    
    @staticmethod
    def info(title: str, content: str) -> Optional[Panel]:
        """Info panel with title and content."""
        if not RICH_AVAILABLE:
            return None
        return Panel(
            content,
            title=f"[bold]{title}[/bold]",
            border_style="blue",
            box=ROUNDED,
        )


# =============================================================================
# Rich Table Components
# =============================================================================

class AgentOSTables:
    """Rich table templates for AgentOS CLI."""
    
    @staticmethod
    def config_table(settings: Dict[str, str]) -> Optional[Table]:
        """Create configuration table."""
        if not RICH_AVAILABLE:
            return None
        
        table = Table(title="[cyan]AgentOS Configuration[/cyan]", box=ROUNDED)
        table.add_column("Setting", style="cyan bold", no_wrap=True)
        table.add_column("Value", style="green")
        
        for key, value in settings.items():
            table.add_row(key, str(value))
        
        return table
    
    @staticmethod
    def skills_table(skills: List[Dict[str, str]]) -> Optional[Table]:
        """Create skills table."""
        if not RICH_AVAILABLE:
            return None
        
        table = Table(title="[cyan]Available Skills[/cyan]", box=ROUNDED)
        table.add_column("#", style="dim", justify="right", width=4)
        table.add_column("Name", style="cyan bold")
        table.add_column("Category", style="blue")
        table.add_column("Description", style="white")
        
        for i, skill in enumerate(skills, 1):
            table.add_row(
                str(i),
                skill.get("name", ""),
                skill.get("category", ""),
                skill.get("description", "")[:50] + "..." if len(skill.get("description", "")) > 50 else skill.get("description", ""),
            )
        
        return table
    
    @staticmethod
    def sessions_table(sessions: List[Dict[str, Any]]) -> Optional[Table]:
        """Create sessions table."""
        if not RICH_AVAILABLE:
            return None
        
        table = Table(title="[cyan]Active Sessions[/cyan]", box=ROUNDED)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Task", style="white")
        table.add_column("Status", style="green")
        table.add_column("Steps", style="yellow", justify="right")
        
        for session in sessions:
            status = session.get("status", "unknown")
            status_color = "green" if status == "completed" else "yellow"
            table.add_row(
                session.get("id", ""),
                session.get("task", "")[:30],
                f"[{status_color}]{status}[/{status_color}]",
                str(session.get("steps", 0)),
            )
        
        return table
    
    @staticmethod
    def commands_table(commands: List[Dict[str, str]]) -> Optional[Table]:
        """Create help/commands table."""
        if not RICH_AVAILABLE:
            return None
        
        table = Table(title="[cyan]Available Commands[/cyan]", box=ROUNDED)
        table.add_column("Command", style="cyan bold")
        table.add_column("Description", style="white")
        
        for cmd in commands:
            table.add_row(
                cmd.get("command", ""),
                cmd.get("description", ""),
            )
        
        return table


# =============================================================================
# Progress Indicators
# =============================================================================

class AgentOSProgress:
    """Progress bar and spinner templates."""
    
    @staticmethod
    def spinning(title: str = "Processing..."):
        """Create spinning progress indicator."""
        if not RICH_AVAILABLE:
            print(f"⟳ {title}")
            return None
        
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    
    @staticmethod
    def task_progress():
        """Create task progress bar."""
        if not RICH_AVAILABLE:
            return None
        
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            console=console,
        )


# =============================================================================
# Interactive Menu
# =============================================================================

class AgentOSMenu:
    """Interactive menu system for AgentOS CLI."""
    
    @staticmethod
    def main_menu() -> List[Dict[str, str]]:
        """Return main menu options."""
        return [
            {"id": "run", "label": "Run Task", "desc": "Execute a task with AgentOS", "key": "r"},
            {"id": "sessions", "label": "Sessions", "desc": "Manage active sessions", "key": "s"},
            {"id": "config", "label": "Configuration", "desc": "View/edit configuration", "key": "c"},
            {"id": "skills", "label": "Skills", "desc": "Browse available skills", "key": "k"},
            {"id": "help", "label": "Help", "desc": "Show help information", "key": "h"},
            {"id": "quit", "label": "Quit", "desc": "Exit AgentOS", "key": "q"},
        ]
    
    @staticmethod
    def render_menu(options: List[Dict[str, str]], title: str = "Menu") -> str:
        """Render text-based menu."""
        lines = [
            "",
            f"  {title}",
            "  " + "=" * 40,
            "",
        ]
        
        for opt in options:
            lines.append(f"  [{opt['key']}] {opt['label']:<15} - {opt['desc']}")
        
        lines.append("")
        lines.append("  Select option: ")
        
        return "\n".join(lines)
    
    @staticmethod
    def select_option(prompt: str = "Select option") -> str:
        """Interactive menu selection."""
        if not RICH_AVAILABLE:
            return Prompt.ask(prompt)
        
        return Prompt.ask(
            f"[cyan]{prompt}[/cyan]",
            choices=[o["key"] for o in AgentOSMenu.main_menu()],
            show_choices=False,
        )


# =============================================================================
# Helper Functions
# =============================================================================

def print_banner(text: str = "AgentOS"):
    """Print ASCII art banner to console."""
    if RICH_AVAILABLE and console:
        banner = AgentOSBanner.render(text, "slant")
        console.print(f"[cyan]{banner}[/cyan]")
    else:
        print(f">>> {text} <<<")


def print_success(message: str):
    """Print success message."""
    if RICH_AVAILABLE and console:
        console.print(AgentOSPanels.success(message))
    else:
        print(f"✓ {message}")


def print_error(message: str):
    """Print error message."""
    if RICH_AVAILABLE and console:
        console.print(AgentOSPanels.error(message))
    else:
        print(f"✗ {message}")


def print_warning(message: str):
    """Print warning message."""
    if RICH_AVAILABLE and console:
        console.print(AgentOSPanels.warning(message))
    else:
        print(f"⚠ {message}")


def print_table(table):
    """Print Rich table."""
    if RICH_AVAILABLE and console and table:
        console.print(table)


def print_panel(panel):
    """Print Rich panel."""
    if RICH_AVAILABLE and console and panel:
        console.print(panel)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "AgentOSBanner",
    "AgentOSPanels", 
    "AgentOSTables",
    "AgentOSProgress",
    "AgentOSMenu",
    "print_banner",
    "print_success", 
    "print_error",
    "print_warning",
    "print_table",
    "print_panel",
    "RICH_AVAILABLE",
]