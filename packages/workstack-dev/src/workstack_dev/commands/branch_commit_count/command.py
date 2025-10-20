"""Count commits on current branch since Graphite parent."""

import subprocess

import click


@click.command(name="branch-commit-count")
def branch_commit_count_command() -> None:
    """Count commits on current branch since Graphite parent."""
    # Get parent branch using gt parent
    result = subprocess.run(
        ["gt", "parent"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Check for errors (LBYL pattern)
    if result.returncode != 0 or not result.stdout.strip():
        click.echo(
            "Error: No Graphite parent found. "
            "Use 'gt parent' to verify branch is tracked by Graphite.",
            err=True,
        )
        raise SystemExit(1)

    # Get merge base
    parent_branch = result.stdout.strip()
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", parent_branch],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Count commits
    count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD", f"^{merge_base}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Output result
    click.echo(count)
