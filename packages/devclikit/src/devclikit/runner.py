"""Execute PEP 723 inline scripts with uv."""

import shutil
import subprocess
from pathlib import Path

import click

from devclikit.exceptions import ScriptExecutionError


def run_pep723_script(
    script_path: Path | str,
    args: list[str] | None = None,
    *,
    check: bool = True,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Execute a PEP 723 inline script using uv run.

    Args:
        script_path: Path to the script.py file
        args: Optional arguments to pass to the script
        check: Raise exception on non-zero exit (default: True)
        capture_output: Capture stdout/stderr (default: False)
        env: Optional environment variables

    Returns:
        CompletedProcess instance

    Raises:
        ScriptExecutionError: If check=True and execution fails
        FileNotFoundError: If script or uv is not found
    """
    script_path = Path(script_path)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Check if uv is installed before attempting to run
    if not shutil.which("uv"):
        click.echo(
            "Error: 'uv' is not installed. Install it with:",
            err=True,
        )
        click.echo("  curl -LsSf https://astral.sh/uv/install.sh | sh", err=True)
        raise SystemExit(1)

    cmd = ["uv", "run", str(script_path)]
    if args:
        cmd.extend(args)

    # Error boundary: Handle script execution failures
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            env=env,
        )
        return result

    except subprocess.CalledProcessError as e:
        if check:
            raise ScriptExecutionError(f"Script failed with exit code {e.returncode}") from e
        raise


def validate_pep723_script(script_path: Path) -> bool:
    """Check if a file is a valid PEP 723 inline script.

    Validates:
    - File has .py extension
    - Contains PEP 723 metadata block
    - Has required fields (dependencies, requires-python)

    Args:
        script_path: Path to script file

    Returns:
        True if valid PEP 723 script
    """
    if script_path.suffix != ".py":
        return False

    if not script_path.exists():
        return False

    content = script_path.read_text(encoding="utf-8")

    # Check for PEP 723 marker
    if "# /// script" not in content:
        return False

    # Basic validation of required fields
    has_dependencies = "dependencies" in content
    has_python_version = "requires-python" in content

    return has_dependencies and has_python_version
