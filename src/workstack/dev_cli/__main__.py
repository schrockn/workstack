"""Development CLI entry point."""

from pathlib import Path

from dev_cli_core import create_cli

cli = create_cli(
    name="workstack-dev",
    description="Development tools for workstack.",
    commands_dir=Path(__file__).parent / "commands",
    add_completion=False,
)

if __name__ == "__main__":
    cli()
