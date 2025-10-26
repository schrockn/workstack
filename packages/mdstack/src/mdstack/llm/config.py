import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: str  # 'anthropic'
    models: dict[str, str]  # File type -> model mapping (lookup, tests, architecture)
    api_key: str
    max_tokens: int = 4000
    temperature: float = 0.1
    verbose: bool = False
    enable_caching: bool = True
    cache_ttl: str = "5m"  # "5m" or "1h"

    def get_model_for_file_type(self, file_type: str) -> str:
        """Get model for specific file type (lookup, tests, architecture)."""
        if file_type not in self.models:
            raise ValueError(
                f"No model configured for file type '{file_type}'. "
                f"Available types: {list(self.models.keys())}"
            )
        return self.models[file_type]


def load_config(config_path: Path | None = None) -> LLMConfig:
    """Load LLM configuration from file or environment."""
    if config_path is None:
        # Search up the directory tree for .mdstack.config.yaml
        current = Path.cwd()
        while current != current.parent:
            candidate = current / ".mdstack.config.yaml"
            if candidate.exists():
                config_path = candidate
                break
            current = current.parent

        # If not found, use default path (won't exist, will fallto environment)
        if config_path is None:
            config_path = Path.cwd() / ".mdstack.config.yaml"

    if config_path.exists():
        data = yaml.safe_load(config_path.read_text())
        llm_config = data.get("llm", {})

        # Get API key from environment variable
        api_key_env = llm_config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")

        # Parse models configuration (supports both new and old format)
        models_config = llm_config.get("models")
        if models_config:
            # New format: per-file-type models
            # Use config values, with fallback defaults only if keys are missing
            default_model = "claude-sonnet-4-20250514"
            models = {
                "lookup": models_config.get("lookup", default_model),
                "tests": models_config.get("tests", default_model),
                "architecture": models_config.get("architecture", default_model),
            }
        else:
            # Old format: single model for all file types (backward compatibility)
            single_model = llm_config.get("model", "claude-sonnet-4-20250514")
            models = {
                "lookup": single_model,
                "tests": single_model,
                "architecture": single_model,
            }

        return LLMConfig(
            provider=llm_config.get("provider", "anthropic"),
            models=models,
            api_key=api_key,
            max_tokens=llm_config.get("max_tokens", 4000),
            temperature=llm_config.get("temperature", 0.1),
            enable_caching=llm_config.get("enable_caching", True),
            cache_ttl=llm_config.get("cache_ttl", "5m"),
        )
    else:
        # Use environment variables with default models
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("No API key found. Set ANTHROPIC_API_KEY")

        return LLMConfig(
            provider="anthropic",
            models={
                "lookup": "claude-3-5-haiku-20241022",
                "tests": "claude-3-5-haiku-20241022",
                "architecture": "claude-sonnet-4-20250514",
            },
            api_key=api_key,
        )


def create_llm_client(config: LLMConfig, file_type: str):
    """
    Create LLM client from config for specific file type.

    Args:
        config: LLM configuration
        file_type: Type of file to generate (lookup, tests, architecture)
    """
    from mdstack.llm.client import AnthropicClient

    if config.provider != "anthropic":
        raise ValueError(f"Only 'anthropic' provider supported in Phase 1, got: {config.provider}")

    model = config.get_model_for_file_type(file_type)
    return AnthropicClient(api_key=config.api_key, model=model)
