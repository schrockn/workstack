"""Shell completion command for workstack-dev."""

import os
import shutil
import subprocess
import sys

import click


def workstack_dev_command() -> list[str]:
    """Determine how to invoke workstack-dev for completion generation."""
    executable = shutil.which("workstack-dev")
    if executable is not None:
        return [executable]

    return [sys.executable, "-m", "workstack_dev.__main__"]


def emit_completion_script(shell: str) -> None:
    """Generate and print the completion script for the requested shell."""
    env = os.environ.copy()
    env["_WORKSTACK_DEV_COMPLETE"] = f"{shell}_source"

    result = subprocess.run(
        workstack_dev_command(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, err=True, nl=False)

    if result.returncode != 0:
        raise SystemExit(result.returncode)


@click.group(name="completion")
def command() -> None:
    """Generate shell completion scripts for workstack-dev."""


@command.command(name="bash")
def bash() -> None:
    r"""Generate bash completion script.

    \b
    Temporary (current session only):
        source <(workstack-dev completion bash)

    Permanent installation:
        echo 'source <(workstack-dev completion bash)' >> ~/.bashrc
        source ~/.bashrc

    Alternative - install to completion directory:
        workstack-dev completion bash > ~/.local/share/bash-completion/completions/workstack-dev
        # Then restart your shell
    """
    emit_completion_script("bash")


@command.command(name="zsh")
def zsh() -> None:
    r"""Generate zsh completion script.

    \b
    Temporary (current session only):
        source <(workstack-dev completion zsh)

    Permanent installation:
        echo 'source <(workstack-dev completion zsh)' >> ~/.zshrc
        source ~/.zshrc

    Alternative - install to completion directory:
        mkdir -p ~/.zsh/completions
        workstack-dev completion zsh > ~/.zsh/completions/_workstack-dev
        # Add to ~/.zshrc: fpath=(~/.zsh/completions $fpath)
        # Then restart your shell
    """
    emit_completion_script("zsh")


@command.command(name="fish")
def fish() -> None:
    r"""Generate fish completion script.

    \b
    Usage: workstack-dev completion fish | source

    Permanent installation:
        mkdir -p ~/.config/fish/completions
        workstack-dev completion fish > ~/.config/fish/completions/workstack-dev.fish
        # Completions will be loaded automatically in new fish sessions
    """
    emit_completion_script("fish")
