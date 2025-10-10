"""DevCliKit: Framework for building development CLIs."""

from devclikit.cli_factory import create_cli
from devclikit.completion import add_completion_commands
from devclikit.exceptions import CommandLoadError, DevCliFrameworkError, ScriptExecutionError
from devclikit.loader import load_commands
from devclikit.runner import run_pep723_script, validate_pep723_script
from devclikit.utils import ensure_directory, is_valid_command_name

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
