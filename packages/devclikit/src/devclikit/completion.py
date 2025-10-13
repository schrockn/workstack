"""Shell completion support for development CLIs."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click


def _detect_shell() -> str:
    """Auto-detect the current shell from environment.

    Returns:
        Shell name: "bash", "zsh", or "fish"

    Raises:
        SystemExit: If shell cannot be detected
    """
    shell_env = os.environ.get("SHELL", "")
    if "zsh" in shell_env:
        return "zsh"
    if "bash" in shell_env:
        return "bash"
    if "fish" in shell_env:
        return "fish"

    click.echo("Error: Could not detect shell from SHELL environment variable", err=True)
    click.echo("Please specify shell explicitly with --shell option", err=True)
    raise SystemExit(1)


def _get_shell_config(shell: str) -> Path:
    """Get the config file path for a given shell.

    Args:
        shell: Shell name ("bash", "zsh", or "fish")

    Returns:
        Path to the shell's config file
    """
    home = Path.home()

    if shell == "bash":
        # Prefer .bashrc on Linux, .bash_profile on macOS
        bashrc = home / ".bashrc"
        bash_profile = home / ".bash_profile"
        if bashrc.exists():
            return bashrc
        return bash_profile
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "fish":
        return home / ".config" / "fish" / "config.fish"

    raise ValueError(f"Unknown shell: {shell}")


def _get_completion_env_var(cli_name: str) -> str:
    """Generate completion environment variable name from CLI name.

    Args:
        cli_name: Name of the CLI (e.g., "workstack-dev")

    Returns:
        Environment variable name (e.g., "_WORKSTACK_DEV_COMPLETE")
    """
    # Convert cli-name to _CLI_NAME_COMPLETE format
    var_name = cli_name.upper().replace("-", "_")
    return f"_{var_name}_COMPLETE"


def _generate_wrapper_script(cli_name: str, shell: str) -> str:
    """Generate lazy-loading wrapper function for shell completion.

    Creates a wrapper function that:
    1. Checks if completion env var is set (to avoid intercepting completion calls)
    2. Undefines itself
    3. Loads completion if command is available
    4. Executes the actual command

    Args:
        cli_name: Name of the CLI
        shell: Shell type ("bash", "zsh", or "fish")

    Returns:
        Shell script as a string
    """
    env_var = _get_completion_env_var(cli_name)

    if shell == "bash":
        return f"""# Lazy-loading completion wrapper for {cli_name}
{cli_name}() {{
    # Don't intercept if we're running completion
    if [ -n "${{{env_var}}}" ]; then
        command {cli_name} "$@"
        return $?
    fi

    # Remove this wrapper function
    unset -f {cli_name}

    # Load completion if command is available
    if command -v {cli_name} &> /dev/null; then
        source <({cli_name} completion bash 2>/dev/null)
    fi

    # Execute the actual command
    {cli_name} "$@"
}}
"""

    if shell == "zsh":
        return f"""# Lazy-loading completion wrapper for {cli_name}
{cli_name}() {{
    # Don't intercept if we're running completion
    if [[ -n "${{{env_var}}}" ]]; then
        command {cli_name} "$@"
        return $?
    fi

    # Remove this wrapper function
    unfunction {cli_name}

    # Load completion if command is available
    if command -v {cli_name} &> /dev/null; then
        source <({cli_name} completion zsh 2>/dev/null)
    fi

    # Execute the actual command
    {cli_name} "$@"
}}
"""

    if shell == "fish":
        return f"""# Lazy-loading completion wrapper for {cli_name}
function {cli_name}
    # Don't intercept if we're running completion
    if set -q {env_var}
        command {cli_name} $argv
        return $status
    end

    # Remove this wrapper function
    functions -e {cli_name}

    # Load completion if command is available
    if command -v {cli_name} &> /dev/null
        {cli_name} completion fish 2>/dev/null | source
    end

    # Execute the actual command
    {cli_name} $argv
end
"""

    raise ValueError(f"Unknown shell: {shell}")


def _is_completion_installed(config_file: Path, cli_name: str) -> bool:
    """Check if completion is already installed in the config file.

    Args:
        config_file: Path to the shell config file
        cli_name: Name of the CLI

    Returns:
        True if completion marker is found in the config file
    """
    if not config_file.exists():
        return False

    marker = f"# {cli_name} completion - added by devclikit"
    content = config_file.read_text(encoding="utf-8")
    return marker in content


def _append_to_config(config_file: Path, snippet: str, cli_name: str) -> None:
    """Append completion snippet to shell config file.

    Args:
        config_file: Path to the shell config file
        snippet: Shell script snippet to append
        cli_name: Name of the CLI (for marker comment)
    """
    # Check if already installed
    if _is_completion_installed(config_file, cli_name):
        click.echo(f"Completion for {cli_name} is already installed in {config_file}", err=True)
        click.echo("Remove the existing completion block to reinstall", err=True)
        raise SystemExit(1)

    # Create parent directories if needed
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Add marker comment and snippet
    marker = f"# {cli_name} completion - added by devclikit"
    full_snippet = f"\n{marker}\n{snippet}\n"

    # Create file if it doesn't exist, otherwise append
    if config_file.exists():
        with config_file.open("a", encoding="utf-8") as f:
            f.write(full_snippet)
    else:
        config_file.write_text(full_snippet, encoding="utf-8")


def add_completion_commands(cli: click.Group, cli_name: str) -> None:
    """Add completion subcommands to a CLI.

    Adds a 'completion' group with bash/zsh/fish commands.

    Args:
        cli: Click group to add completion commands to
        cli_name: Name of the CLI (used for completion script)
    """

    @cli.group("completion")
    def completion_group() -> None:
        """Generate shell completion scripts.

        Enables tab completion for all commands and options.
        """
        pass

    @completion_group.command("bash")
    def completion_bash() -> None:
        """Generate bash completion script."""
        _generate_completion(cli_name, "bash_source")

    completion_bash.__doc__ = f"""Generate bash completion script for {cli_name}.

        \\b
        For most users, use 'completion install' instead:
          {cli_name} completion install

        \\b
        Direct usage (requires {cli_name} to be in PATH):
          source <({cli_name} completion bash)

        \\b
        To load permanently, add to ~/.bashrc:
          echo 'source <({cli_name} completion bash)' >> ~/.bashrc

        \\b
        Note: For CLIs in virtual environments, use 'completion install'
        which creates a lazy-loading wrapper that works before venv activation.
        """

    @completion_group.command("zsh")
    def completion_zsh() -> None:
        """Generate zsh completion script."""
        _generate_completion(cli_name, "zsh_source")

    completion_zsh.__doc__ = f"""Generate zsh completion script for {cli_name}.

        \\b
        For most users, use 'completion install' instead:
          {cli_name} completion install

        \\b
        Direct usage (requires {cli_name} to be in PATH):
          source <({cli_name} completion zsh)

        \\b
        To load permanently, add to ~/.zshrc:
          echo 'source <({cli_name} completion zsh)' >> ~/.zshrc

        \\b
        Note: For CLIs in virtual environments, use 'completion install'
        which creates a lazy-loading wrapper that works before venv activation.
        """

    @completion_group.command("fish")
    def completion_fish() -> None:
        """Generate fish completion script."""
        _generate_completion(cli_name, "fish_source")

    completion_fish.__doc__ = f"""Generate fish completion script for {cli_name}.

        \\b
        For most users, use 'completion install' instead:
          {cli_name} completion install

        \\b
        Direct usage (requires {cli_name} to be in PATH):
          {cli_name} completion fish | source

        \\b
        To load permanently:
          mkdir -p ~/.config/fish/completions
          {cli_name} completion fish > ~/.config/fish/completions/{cli_name}.fish

        \\b
        Note: For CLIs in virtual environments, use 'completion install'
        which creates a lazy-loading wrapper that works before venv activation.
        """

    @completion_group.command("wrapper")
    @click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
    def completion_wrapper(shell: str) -> None:
        """Generate lazy-loading wrapper function.

        Outputs a shell function that delays loading completion until first use.
        This is useful for CLIs installed in virtual environments.

        SHELL: The shell to generate wrapper for (bash, zsh, or fish)
        """
        wrapper = _generate_wrapper_script(cli_name, shell)
        click.echo(wrapper, nl=False)

    completion_wrapper.__doc__ = f"""Generate lazy-loading wrapper function for {cli_name}.

        \\b
        Useful for CLIs in virtual environments that aren't always in PATH.
        The wrapper delays completion loading until first use.

        \\b
        Usage:
          {cli_name} completion wrapper zsh >> ~/.zshrc

        \\b
        Or use 'completion install' for automated installation.
        """

    @completion_group.command("install")
    @click.option(
        "--shell",
        type=click.Choice(["bash", "zsh", "fish"]),
        help="Shell to install for (auto-detected if not specified)",
    )
    @click.option(
        "--lazy/--no-lazy",
        default=True,
        help="Use lazy-loading wrapper (default: --lazy)",
    )
    @click.option(
        "--force",
        is_flag=True,
        help="Overwrite existing installation",
    )
    def completion_install(shell: str | None, lazy: bool, force: bool) -> None:
        """Install completion to shell config file.

        Automatically detects your shell and adds completion to the appropriate
        config file. Uses lazy-loading by default for virtual environment CLIs.
        """
        # Auto-detect shell if not specified
        if shell is None:
            shell = _detect_shell()

        # Get config file path
        config_file = _get_shell_config(shell)

        # Check if already installed (unless --force)
        if not force and _is_completion_installed(config_file, cli_name):
            click.echo(f"Completion for {cli_name} is already installed in {config_file}")
            click.echo("Use --force to reinstall")
            return

        # Generate snippet
        if lazy:
            snippet = _generate_wrapper_script(cli_name, shell)
        else:
            # Direct completion loading
            if shell == "bash":
                snippet = f"source <({cli_name} completion bash)"
            elif shell == "zsh":
                snippet = f"source <({cli_name} completion zsh)"
            else:  # fish
                snippet = f"{cli_name} completion fish | source"

        # Show what will be added
        click.echo(f"Installing {cli_name} completion to {config_file}")
        click.echo(f"Mode: {'lazy-loading wrapper' if lazy else 'direct loading'}")
        click.echo()

        # Install (will raise SystemExit if already installed and not force)
        if force and _is_completion_installed(config_file, cli_name):
            click.echo(
                "Note: Completion already exists. Add --force logic to remove old version first."
            )
            click.echo("For now, please manually remove the existing completion block.")
            raise SystemExit(1)

        _append_to_config(config_file, snippet, cli_name)

        click.echo()
        click.echo("✓ Completion installed successfully!")
        click.echo()
        click.echo("To activate, run:")
        click.echo(f"  source {config_file}")

    @completion_group.command("status")
    def completion_status() -> None:
        """Check completion installation status.

        Displays diagnostic information about completion setup and suggests
        fixes if completion is not working.
        """
        # Detect shell
        try:
            shell = _detect_shell()
            click.echo(f"Detected shell: {shell}")
        except SystemExit:
            click.echo("Could not detect shell from SHELL environment variable")
            return

        # Get config file
        config_file = _get_shell_config(shell)
        click.echo(f"Config file: {config_file}")

        # Check if config file exists
        if config_file.exists():
            click.echo("Config file exists: yes")
        else:
            click.echo("Config file exists: no")

        # Check if CLI is in PATH
        cli_exe = shutil.which(cli_name)
        if cli_exe:
            click.echo(f"CLI in PATH: yes ({cli_exe})")
        else:
            click.echo("CLI in PATH: no")

        # Check if completion is installed
        installed = _is_completion_installed(config_file, cli_name)
        click.echo(f"Completion installed: {'yes' if installed else 'no'}")

        # Provide guidance
        click.echo()
        if not installed:
            click.echo("Next steps:")
            click.echo(f"  Run: {cli_name} completion install")
        elif not cli_exe:
            click.echo("Note: CLI not in PATH. Ensure virtual environment is activated.")
        else:
            click.echo("Completion appears to be set up correctly.")
            click.echo(f"If completion isn't working, try: source {config_file}")


def _generate_completion(cli_name: str, shell_type: str) -> None:
    """Generate completion script by invoking CLI with completion env var."""
    # Find the CLI executable
    cli_exe = shutil.which(cli_name)
    if not cli_exe:
        cli_exe = sys.argv[0]

    # Generate completion script
    env = os.environ.copy()
    env[f"_{cli_name.upper().replace('-', '_')}_COMPLETE"] = shell_type

    result = subprocess.run(
        [cli_exe],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    click.echo(result.stdout, nl=False)
