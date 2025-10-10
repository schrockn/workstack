"""Dev CLI framework - public API."""

from dev_cli_core.cli_factory import create_cli
from dev_cli_core.completion import add_completion_commands
from dev_cli_core.exceptions import CommandLoadError, DevCliFrameworkError, ScriptExecutionError
from dev_cli_core.loader import load_commands
from dev_cli_core.runner import run_pep723_script, validate_pep723_script
from dev_cli_core.utils import ensure_directory, is_valid_command_name

__all__ = [
    # Factory
    "create_cli",
    # Loader
    "load_commands",
    # Runner
    "run_pep723_script",
    "validate_pep723_script",
    # Completion
    "add_completion_commands",
    # Utils
    "ensure_directory",
    "is_valid_command_name",
    # Exceptions
    "DevCliFrameworkError",
    "CommandLoadError",
    "ScriptExecutionError",
]
