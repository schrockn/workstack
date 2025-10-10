"""Hello command."""

from pathlib import Path

import click

from devclikit import run_pep723_script


@click.command(name="hello")
@click.option("--name", "-n", default="World", help="Name to greet")
@click.option("--uppercase", "-u", is_flag=True, help="Convert output to uppercase")
def command(name: str, uppercase: bool) -> None:
    """Say hello to someone."""
    script_path = Path(__file__).parent / "script.py"

    args = ["--name", name]
    if uppercase:
        args.append("--uppercase")

    run_pep723_script(script_path, args)
