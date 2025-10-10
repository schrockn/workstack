"""Hello World CLI - dev_cli_core example."""

from pathlib import Path

from dev_cli_core import create_cli

# Create CLI with automatic command discovery
cli = create_cli(
    name="hello-world",
    description="Simple hello world CLI example",
    commands_dir=Path(__file__).parent / "commands",
    version="1.0.0",
)

if __name__ == "__main__":
    cli()
