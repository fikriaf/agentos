"""LLM provider configurations."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Provider:
    """LLM Provider configuration."""

    name: str
    models: list[str]
    api_key_env: str
    default_model: str


# Known providers
PROVIDERS = {
    "anthropic": Provider(
        name="Anthropic",
        models=[
            "claude-3-5-sonnet-4-7",
            "claude-3-5-haiku-3",
            "claude-opus-4-5",
        ],
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-3-5-sonnet-4-7",
    ),
    "openai": Provider(
        name="OpenAI",
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o",
    ),
    "google": Provider(
        name="Google",
        models=[
            "gemini-2-5-flash",
            "gemini-2-5-pro",
            "gemini-2-0-flash-exp",
        ],
        api_key_env="GOOGLE_API_KEY",
        default_model="gemini-2-5-flash",
    ),
    "deepseek": Provider(
        name="DeepSeek",
        models=[
            "deepseek-chat-v3",
            "deepseek-reasoner",
        ],
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat-v3",
    ),
}


def get_provider_from_model(model: str) -> Optional[Provider]:
    """Get provider from model name.

    Args:
        model: Model name (e.g., "claude-3-5-sonnet-4-7")

    Returns:
        Provider or None
    """
    model_lower = model.lower()

    for provider in PROVIDERS.values():
        for m in provider.models:
            if m in model_lower:
                return provider

    return None


def format_model_name(provider: str, model: str) -> str:
    """Format model name for OpenRouter.

    Args:
        provider: Provider name
        model: Model name

    Returns:
        OpenRouter format model name
    """
    # OpenRouter uses "provider/model" format
    provider_map = {
        "anthropic": "anthropic",
        "openai": "openai",
        "google": "google",
        "deepseek": "deepseek",
    }

    p = provider_map.get(provider.lower(), provider.lower())
    return f"{p}/{model}"


def list_available_models() -> list[str]:
    """List all available models.

    Returns:
        List of model names
    """
    models = []
    for provider in PROVIDERS.values():
        models.extend(provider.models)
    return sorted(models)
