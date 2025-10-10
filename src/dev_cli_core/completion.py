"""Shell completion support for development CLIs."""

import os
import shutil
import subprocess
import sys

import click


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
        To load completions in your current shell:
          source <({cli_name} completion bash)

        \\b
        To load permanently, add to ~/.bashrc:
          echo 'source <({cli_name} completion bash)' >> ~/.bashrc
        """

    @completion_group.command("zsh")
    def completion_zsh() -> None:
        """Generate zsh completion script."""
        _generate_completion(cli_name, "zsh_source")

    completion_zsh.__doc__ = f"""Generate zsh completion script for {cli_name}.

        \\b
        To load completions in your current shell:
          source <({cli_name} completion zsh)

        \\b
        To load permanently, add to ~/.zshrc:
          echo 'source <({cli_name} completion zsh)' >> ~/.zshrc
        """

    @completion_group.command("fish")
    def completion_fish() -> None:
        """Generate fish completion script."""
        _generate_completion(cli_name, "fish_source")

    completion_fish.__doc__ = f"""Generate fish completion script for {cli_name}.

        \\b
        To load completions in your current shell:
          {cli_name} completion fish | source

        \\b
        To load permanently:
          mkdir -p ~/.config/fish/completions
          {cli_name} completion fish > ~/.config/fish/completions/{cli_name}.fish
        """


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
