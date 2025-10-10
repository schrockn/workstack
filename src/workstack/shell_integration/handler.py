from dataclasses import dataclass
from pathlib import Path
from typing import Final

from click.testing import CliRunner

from workstack.commands.create import create
from workstack.commands.switch import switch_cmd
from workstack.commands.sync import sync_cmd
from workstack.context import create_context
from workstack.debug import debug_log
from workstack.shell_utils import cleanup_stale_scripts

PASSTHROUGH_MARKER: Final[str] = "__WORKSTACK_PASSTHROUGH__"


@dataclass(frozen=True)
class ShellIntegrationResult:
    """Result returned by shell integration handlers."""

    passthrough: bool
    script: str | None
    exit_code: int


def _invoke_hidden_command(command_name: str, args: tuple[str, ...]) -> ShellIntegrationResult:
    """Invoke a command with --script flag for shell integration.

    If args contain help flags or explicit --script, passthrough to regular command.
    Otherwise, add --script flag and capture the activation script.
    """
    # Check if help flags or --script are present - these should pass through
    if "-h" in args or "--help" in args or "--script" in args:
        return ShellIntegrationResult(passthrough=True, script=None, exit_code=0)

    # Map command names to their Click commands
    command_map = {
        "switch": switch_cmd,
        "sync": sync_cmd,
        "create": create,
    }

    command = command_map.get(command_name)
    if command is None:
        return ShellIntegrationResult(passthrough=True, script=None, exit_code=0)

    # Add --script flag to get activation script
    script_args = list(args) + ["--script"]

    debug_log(f"Handler: Invoking {command_name} with args: {script_args}")

    # Clean up stale scripts before running (opportunistic cleanup)
    cleanup_stale_scripts(max_age_seconds=3600)

    runner = CliRunner()
    result = runner.invoke(
        command,
        script_args,
        obj=create_context(dry_run=False),
        standalone_mode=False,
    )

    exit_code = int(result.exit_code)

    # If command failed, passthrough to show proper error
    if exit_code != 0:
        return ShellIntegrationResult(passthrough=True, script=None, exit_code=exit_code)

    # Output is now a file path, not script content
    script_path = result.output.strip() if result.output else None

    debug_log(f"Handler: Got script_path={script_path}, exit_code={exit_code}")
    if script_path:
        script_exists = Path(script_path).exists()
        debug_log(f"Handler: Script exists? {script_exists}")

    return ShellIntegrationResult(passthrough=False, script=script_path, exit_code=exit_code)


def handle_shell_request(args: tuple[str, ...]) -> ShellIntegrationResult:
    """Dispatch shell integration handling based on the original CLI invocation."""
    if not args:
        return ShellIntegrationResult(passthrough=True, script=None, exit_code=0)

    command_name = args[0]
    command_args = tuple(args[1:])

    return _invoke_hidden_command(command_name, command_args)
