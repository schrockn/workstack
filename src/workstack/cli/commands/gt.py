"""Graphite integration commands for workstack.

Provides machine-readable access to Graphite metadata for scripting and automation.
"""

import json
from dataclasses import asdict
from pathlib import Path

import click

from workstack.cli.core import discover_repo_context
from workstack.core.context import WorkstackContext


@click.group("gt")
@click.pass_obj
def gt_group(ctx: WorkstackContext) -> None:
    """Graphite integration commands (requires use-graphite enabled)."""
    pass


@gt_group.command("branches")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
@click.pass_obj
def gt_branches_cmd(ctx: WorkstackContext, format: str) -> None:
    """List all gt-tracked branches.

    By default, outputs a simple list of branch names (one per line).
    Use --format json for structured output with full metadata.

    Examples:
        $ workstack gt branches
        main
        feature-1
        feature-2

        $ workstack gt branches --format json
        {
          "branches": [
            {
              "name": "main",
              "parent": null,
              "children": ["feature-1"],
              "is_trunk": true,
              "commit_sha": "abc123..."
            }
          ]
        }

    Requires:
        - Graphite enabled (use_graphite config)
        - Valid .git/.graphite_cache_persist file
    """
    # Check if graphite is enabled
    if not ctx.global_config_ops.get_use_graphite():
        click.echo(
            "Error: Graphite not enabled. Run 'workstack config set use_graphite true'",
            err=True,
        )
        raise SystemExit(1)

    # Discover repository
    repo = discover_repo_context(ctx, Path.cwd())

    # Get branches from GraphiteOps
    branches_dict = ctx.graphite_ops.get_all_branches(ctx.git_ops, repo.root)

    if format == "json":
        # Convert to list of dicts for JSON output
        branches_list = [asdict(metadata) for metadata in branches_dict.values()]
        output = {"branches": branches_list}
        click.echo(json.dumps(output, indent=2))
    else:
        # Text format: simple list of branch names
        for branch_name in sorted(branches_dict.keys()):
            click.echo(branch_name)
