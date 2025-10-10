"""Shell completion command for workstack-dev."""

from pathlib import Path

import click

from dev_cli_core import run_pep723_script


@click.group(name="completion")
def command() -> None:
    """Generate shell completion scripts for workstack-dev.

    Enables tab completion for all workstack-dev commands and options.
    """
    pass


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
    script_path = Path(__file__).parent / "script.py"
    if not script_path.exists():
        click.echo(f"Error: Script not found at {script_path}", err=True)
        raise SystemExit(1)
    result = run_pep723_script(script_path, ["bash"], capture_output=True)
    click.echo(result.stdout, nl=False)


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
    script_path = Path(__file__).parent / "script.py"
    if not script_path.exists():
        click.echo(f"Error: Script not found at {script_path}", err=True)
        raise SystemExit(1)
    result = run_pep723_script(script_path, ["zsh"], capture_output=True)
    click.echo(result.stdout, nl=False)


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
    script_path = Path(__file__).parent / "script.py"
    if not script_path.exists():
        click.echo(f"Error: Script not found at {script_path}", err=True)
        raise SystemExit(1)
    result = run_pep723_script(script_path, ["fish"], capture_output=True)
    click.echo(result.stdout, nl=False)
