"""Configuration management for AgentOS."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class AgentOSConfig:
    """AgentOS configuration."""

    # LLM settings
    model: str = "minimax-m2.5-free"
    api_key: str = ""
    base_url: str = "https://opencode.ai/zen/v1"
    max_tokens: int = 65000
    temperature: float = 0.7

    # Execution settings
    max_steps: int = 100
    default_budget: float = 1.0
    auto_confirm: bool = False

    # Memory settings
    memory_persist_dir: str = "~/.agentos/memory"
    workspace_dir: str = "~/.agentos/workspace"
    snapshot_interval: int = 10

    # Safety settings
    safety_enabled: bool = True
    block_dangerous: bool = True

    @classmethod
    def from_file(cls, path: Path) -> "AgentOSConfig":
        """Load config from file."""
        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()

    def to_file(self, path: Path) -> None:
        """Save config to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(asdict(self), f, default_flow_style=False)

    @property
    def config_dir(self) -> Path:
        """Get config directory."""
        return Path.home() / ".agentos"

    @property
    def config_file(self) -> Path:
        """Get config file path."""
        return self.config_dir / "config.yaml"


def get_config() -> AgentOSConfig:
    """Get current config."""
    config = AgentOSConfig()
    return config.from_file(config.config_file)


def save_config(config: AgentOSConfig) -> None:
    """Save config."""
    config.to_file(config.config_file)
