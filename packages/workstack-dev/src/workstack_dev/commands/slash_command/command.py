"""Execute Claude Code slash commands from the command line."""

import subprocess
import sys
from pathlib import Path

import click


def find_command_file(command_name: str) -> Path | None:
    """
    Find a slash command file in project or user directories.

    Converts namespace separators (: or /) to directory paths.
    Example: "gt:submit-branch" -> .claude/commands/gt/submit-branch.md

    Args:
        command_name: Name of the slash command (e.g., "gt:submit-branch")

    Returns:
        Path to the command file if found, None otherwise
    """
    # Convert namespace separators to path separators
    command_path = command_name.replace(":", "/").replace("//", "/")

    # Add .md extension if not present
    if not command_path.endswith(".md"):
        command_path += ".md"

    # Search locations in priority order
    search_paths = [
        Path.cwd() / ".claude" / "commands" / command_path,  # Project
        Path.home() / ".claude" / "commands" / command_path,  # User
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def strip_frontmatter(content: str) -> str:
    """
    Remove YAML frontmatter from markdown content.

    Frontmatter is defined as content between two '---' lines at the start.

    Args:
        content: Markdown content that may contain frontmatter

    Returns:
        Content with frontmatter removed
    """
    lines = content.split("\n")

    # Check if file starts with frontmatter
    if not lines or lines[0].strip() != "---":
        return content

    # Find the closing ---
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            # Return everything after the closing ---
            return "\n".join(lines[i + 1 :]).strip()

    # No closing ---, return original content
    return content


def process_arguments(prompt: str, arguments: list[str]) -> str:
    """
    Replace $ARGUMENTS placeholder in the prompt with provided arguments.

    Args:
        prompt: The command prompt template
        arguments: List of arguments to substitute

    Returns:
        Processed prompt with arguments substituted
    """
    if not arguments:
        # If no arguments provided but $ARGUMENTS exists, warn user
        if "$ARGUMENTS" in prompt:
            click.echo("Warning: Command expects arguments but none provided", err=True)
            click.echo("The $ARGUMENTS placeholder will be replaced with empty string", err=True)
            return prompt.replace("$ARGUMENTS", "")
        return prompt

    # Join all arguments into a single string
    args_string = " ".join(arguments)

    # Replace $ARGUMENTS with the actual arguments
    return prompt.replace("$ARGUMENTS", args_string)


@click.command(name="slash-command")
@click.argument("command_name")
@click.argument("command_args", nargs=-1)
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "stream-json"]),
    default="stream-json",
    help="Claude output format (default: stream-json)",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def slash_command_command(
    command_name: str, command_args: tuple[str, ...], output_format: str, verbose: bool
) -> None:
    """
    Execute a Claude Code slash command in headless mode.

    COMMAND_NAME: Name of the slash command (e.g., "gt:submit-branch", "issue")

    COMMAND_ARGS: Arguments to pass to the command (replaces $ARGUMENTS)

    Examples:

        workstack-dev slash-command "gt:submit-branch"

        workstack-dev slash-command "issue" "123"

        workstack-dev slash-command "review" "src/main.py"

        workstack-dev slash-command "analyze" "performance issues" --verbose
    """
    # Find the command file
    command_file = find_command_file(command_name)

    if command_file is None:
        click.echo(f"Error: Command '{command_name}' not found", err=True)
        click.echo("\nSearched in:", err=True)
        click.echo(f"  - {Path.cwd() / '.claude' / 'commands'}", err=True)
        click.echo(f"  - {Path.home() / '.claude' / 'commands'}", err=True)
        raise SystemExit(1)

    # Read and process the command file
    content = command_file.read_text(encoding="utf-8")

    if not content:
        click.echo(f"Error: Command file '{command_file}' is empty", err=True)
        raise SystemExit(1)

    prompt = strip_frontmatter(content)

    if not prompt:
        click.echo(f"Error: Command file '{command_file}' contains only frontmatter", err=True)
        raise SystemExit(1)

    # Process arguments
    prompt = process_arguments(prompt, list(command_args))

    # Build claude command
    # Note: Claude CLI requires --print for non-interactive mode
    # When using --output-format=stream-json with --print, --verbose is required
    cmd = ["claude", "--print", "--output-format", output_format]

    # stream-json requires verbose when using --print
    if output_format == "stream-json" or verbose:
        cmd.append("--verbose")

    # Add prompt as final positional argument
    cmd.append(prompt)

    # Check if claude command exists
    try:
        subprocess.run(["which", "claude"], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        click.echo("Error: 'claude' command not found. Is Claude Code installed?", err=True)
        raise SystemExit(1) from e

    # Execute claude command
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Stream to stdout/stderr
            text=True,
            check=True,
        )
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        # Claude command failed, exit with its return code
        sys.exit(e.returncode)
