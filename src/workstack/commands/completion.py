import os
import shutil
import subprocess
import sys

import click


@click.group("completion")
def completion_group() -> None:
    """Generate shell completion scripts."""


@completion_group.command("bash")
def completion_bash() -> None:
    """Generate bash completion script.

    \b
    For automatic setup of both completion and auto-activation:
      workstack init --shell

    \b
    To load completions in your current shell session:
      source <(workstack completion bash)

    \b
    To load completions permanently, add to your ~/.bashrc:
      echo 'source <(workstack completion bash)' >> ~/.bashrc

    \b
    Alternatively, you can save the completion script to bash_completion.d:
      workstack completion bash > /usr/local/etc/bash_completion.d/workstack

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "bash_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)


@completion_group.command("zsh")
def completion_zsh() -> None:
    """Generate zsh completion script.

    \b
    For automatic setup of both completion and auto-activation:
      workstack init --shell

    \b
    To load completions in your current shell session:
      source <(workstack completion zsh)

    \b
    To load completions permanently, add to your ~/.zshrc:
      echo 'source <(workstack completion zsh)' >> ~/.zshrc

    \b
    Note: Make sure compinit is called in your ~/.zshrc after loading completions.

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "zsh_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)


@completion_group.command("fish")
def completion_fish() -> None:
    """Generate fish completion script.

    \b
    For automatic setup of both completion and auto-activation:
      workstack init --shell

    \b
    To load completions in your current shell session:
      workstack completion fish | source

    \b
    To load completions permanently:
      mkdir -p ~/.config/fish/completions && \\
      workstack completion fish > ~/.config/fish/completions/workstack.fish

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "fish_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)
