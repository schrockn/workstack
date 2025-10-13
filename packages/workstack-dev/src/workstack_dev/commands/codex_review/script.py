#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Codex-driven code review implementation.

Performs comprehensive code review by:
1. Auto-detecting base branch (Graphite parent → main → HEAD~1)
2. Loading prompt template and substituting variables
3. Executing Codex with repository standards context
4. Displaying review summary to terminal
"""

# pyright: reportMissingImports=false

import subprocess
from datetime import datetime
from pathlib import Path

import click


def detect_base_branch(explicit_base: str | None) -> str:
    """Detect appropriate base branch for comparison.

    Args:
        explicit_base: Explicitly provided base branch, or None

    Returns:
        Base branch name to use for comparison

    Priority order:
    1. Explicit argument if provided
    2. HEAD~1 if on trunk (main/master)
    3. Graphite parent if available
    4. Fallback to main
    """
    if explicit_base:
        return explicit_base

    current = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # On trunk branch - compare with previous commit
    if current in ("main", "master"):
        return "HEAD~1"

    # Try Graphite parent
    result = subprocess.run(
        ["gt", "parent"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    # Fallback to main
    return "main"


def generate_output_filename(current_branch: str, custom_output: str | None) -> str:
    """Generate output filename with sanitized branch name.

    Args:
        current_branch: Current git branch name
        custom_output: Custom output path if provided

    Returns:
        Output filename (sanitized and timestamped if auto-generated)
    """
    if custom_output:
        return custom_output

    # Sanitize branch name for filesystem (fix for branches with slashes)
    sanitized_branch = current_branch.replace("/", "__").replace(":", "__")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"code-review-{sanitized_branch}-{timestamp}.md"


def load_prompt_template(template_path: Path) -> str:
    """Load prompt template from file.

    Args:
        template_path: Path to prompt.txt template file

    Returns:
        Template content as string
    """
    if not template_path.exists():
        click.echo(f"✗ Prompt template not found: {template_path}", err=True)
        raise SystemExit(1)

    return template_path.read_text(encoding="utf-8")


def format_prompt(
    template: str,
    base_branch: str,
    current_branch: str,
    output_file: str,
) -> str:
    """Format prompt template with actual values.

    Args:
        template: Prompt template string with placeholders
        base_branch: Base branch for comparison
        current_branch: Current branch being reviewed
        output_file: Output filename for the review

    Returns:
        Formatted prompt string
    """
    date = datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")

    return template.format(
        base_branch=base_branch,
        current_branch=current_branch,
        output_file=output_file,
        date=date,
    )


@click.command()
@click.option("--base", help="Base branch for comparison")
@click.option("--output", help="Output file path")
def main(base: str | None, output: str | None) -> None:
    """Execute code review workflow."""
    # Detect branches
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    base_branch = detect_base_branch(base)
    output_file = generate_output_filename(current_branch, output)

    click.echo(f"Reviewing: {current_branch} vs {base_branch}")
    click.echo(f"Output: {output_file}\n")

    # Load and format prompt template
    template_path = Path(__file__).parent / "prompt.txt"
    template = load_prompt_template(template_path)
    codex_prompt = format_prompt(template, base_branch, current_branch, output_file)

    # Execute Codex
    result = subprocess.run(
        ["codex", "exec", "--sandbox", "workspace-write", codex_prompt],
        check=True,
        capture_output=False,  # Let output stream to terminal
    )

    if result.returncode == 0:
        click.echo(f"\n✓ Review complete! Saved to {output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.echo("\n✗ Interrupted by user", err=True)
        raise SystemExit(130) from None
