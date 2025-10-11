from pathlib import Path

import click

from workstack.cli.config import LoadedConfig, load_config
from workstack.cli.core import discover_repo_context, ensure_work_dir
from workstack.core.context import WorkstackContext


def _get_env_value(cfg: LoadedConfig, parts: list[str], key: str) -> None:
    """Handle env.* configuration keys.

    Prints the value or exits with error if key not found.
    """
    if len(parts) != 2:
        click.echo(f"Invalid key: {key}", err=True)
        raise SystemExit(1)

    if parts[1] not in cfg.env:
        click.echo(f"Key not found: {key}", err=True)
        raise SystemExit(1)

    click.echo(cfg.env[parts[1]])


def _get_post_create_value(cfg: LoadedConfig, parts: list[str], key: str) -> None:
    """Handle post_create.* configuration keys.

    Prints the value or exits with error if key not found.
    """
    if len(parts) != 2:
        click.echo(f"Invalid key: {key}", err=True)
        raise SystemExit(1)

    # Handle shell subkey
    if parts[1] == "shell":
        if not cfg.post_create_shell:
            click.echo(f"Key not found: {key}", err=True)
            raise SystemExit(1)
        click.echo(cfg.post_create_shell)
        return

    # Handle commands subkey
    if parts[1] == "commands":
        for cmd in cfg.post_create_commands:
            click.echo(cmd)
        return

    # Unknown subkey
    click.echo(f"Key not found: {key}", err=True)
    raise SystemExit(1)


@click.group("config")
def config_group() -> None:
    """Manage workstack configuration."""


@config_group.command("list")
@click.option(
    "--filter",
    help="Filter config keys by prefix (e.g., 'rebase' for rebase.* keys)",
)
@click.pass_obj
def config_list(ctx: WorkstackContext, filter: str | None) -> None:
    """Print a list of configuration keys and values."""
    # Try to load global config
    try:
        workstacks_root = ctx.global_config_ops.get_workstacks_root()
        use_graphite = ctx.global_config_ops.get_use_graphite()
        show_pr_info = ctx.global_config_ops.get_show_pr_info()
        show_pr_checks = ctx.global_config_ops.get_show_pr_checks()
        rebase_use_stacks = ctx.global_config_ops.get_rebase_use_stacks()
        rebase_auto_test = ctx.global_config_ops.get_rebase_auto_test()
        rebase_preserve_stacks = ctx.global_config_ops.get_rebase_preserve_stacks()
        rebase_conflict_tool = ctx.global_config_ops.get_rebase_conflict_tool()
        rebase_stack_location = ctx.global_config_ops.get_rebase_stack_location()

        click.echo(click.style("Global configuration:", bold=True))

        # Collect all config keys and values
        config_items = [
            ("workstacks_root", str(workstacks_root)),
            ("use_graphite", str(use_graphite).lower()),
            ("show_pr_info", str(show_pr_info).lower()),
            ("show_pr_checks", str(show_pr_checks).lower()),
            ("rebase.useStacks", str(rebase_use_stacks).lower()),
            ("rebase.autoTest", str(rebase_auto_test).lower()),
            ("rebase.preserveStacks", str(rebase_preserve_stacks).lower()),
            ("rebase.conflictTool", rebase_conflict_tool),
            ("rebase.stackLocation", rebase_stack_location),
        ]

        # Apply filter if provided
        if filter:
            config_items = [(k, v) for k, v in config_items if k.startswith(filter)]

        # Display filtered items
        for key, value in config_items:
            click.echo(f"  {key}={value}")

        if filter and not config_items:
            click.echo(f"  (no config keys matching '{filter}')")

    except FileNotFoundError:
        click.echo(click.style("Global configuration:", bold=True))
        click.echo("  (not configured - run 'workstack init' to create)")

    # Try to load repo config
    try:
        repo = discover_repo_context(ctx, Path.cwd())
        work_dir = ensure_work_dir(repo)
        cfg = load_config(work_dir)

        click.echo(click.style("\nRepository configuration:", bold=True))
        if cfg.env:
            for key, value in cfg.env.items():
                click.echo(f"  env.{key}={value}")
        if cfg.post_create_shell:
            click.echo(f"  post_create.shell={cfg.post_create_shell}")
        if cfg.post_create_commands:
            click.echo(f"  post_create.commands={cfg.post_create_commands}")

        if not cfg.env and not cfg.post_create_shell and not cfg.post_create_commands:
            click.echo("  (no configuration - run 'workstack init --repo' to create)")
    except Exception:
        click.echo(click.style("\nRepository configuration:", bold=True))
        click.echo("  (not in a git repository)")


@config_group.command("get")
@click.argument("key", metavar="KEY")
@click.pass_obj
def config_get(ctx: WorkstackContext, key: str) -> None:
    """Print the value of a given configuration key."""
    parts = key.split(".")

    # Handle global config keys
    if parts[0] in ("workstacks_root", "use_graphite", "show_pr_info", "show_pr_checks"):
        try:
            if parts[0] == "workstacks_root":
                click.echo(str(ctx.global_config_ops.get_workstacks_root()))
            elif parts[0] == "use_graphite":
                click.echo(str(ctx.global_config_ops.get_use_graphite()).lower())
            elif parts[0] == "show_pr_info":
                click.echo(str(ctx.global_config_ops.get_show_pr_info()).lower())
            elif parts[0] == "show_pr_checks":
                click.echo(str(ctx.global_config_ops.get_show_pr_checks()).lower())
        except FileNotFoundError as e:
            click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}", err=True)
            raise SystemExit(1) from e
        return

    # Handle rebase.* config keys
    if parts[0] == "rebase":
        if len(parts) != 2:
            click.echo(f"Invalid key: {key}", err=True)
            raise SystemExit(1)

        rebase_keys = {
            "useStacks": lambda: str(ctx.global_config_ops.get_rebase_use_stacks()).lower(),
            "autoTest": lambda: str(ctx.global_config_ops.get_rebase_auto_test()).lower(),
            "preserveStacks": lambda: str(
                ctx.global_config_ops.get_rebase_preserve_stacks()
            ).lower(),
            "conflictTool": lambda: ctx.global_config_ops.get_rebase_conflict_tool(),
            "stackLocation": lambda: ctx.global_config_ops.get_rebase_stack_location(),
        }

        if parts[1] not in rebase_keys:
            click.echo(f"Unknown rebase config key: {parts[1]}", err=True)
            valid_keys = ", ".join(f"rebase.{k}" for k in rebase_keys.keys())
            click.echo(f"Valid keys: {valid_keys}", err=True)
            raise SystemExit(1)

        try:
            click.echo(rebase_keys[parts[1]]())
        except FileNotFoundError as e:
            click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}", err=True)
            raise SystemExit(1) from e
        return

    # Handle repo config keys
    try:
        repo = discover_repo_context(ctx, Path.cwd())
        work_dir = ensure_work_dir(repo)
        cfg = load_config(work_dir)

        if parts[0] == "env":
            _get_env_value(cfg, parts, key)
            return

        if parts[0] == "post_create":
            _get_post_create_value(cfg, parts, key)
            return

        click.echo(f"Invalid key: {key}", err=True)
        raise SystemExit(1)

    except Exception as e:
        if "not in a git repository" in str(e).lower() or "not a git repository" in str(e).lower():
            click.echo("Not in a git repository", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e


@config_group.command("set")
@click.argument("key", metavar="KEY")
@click.argument("value", metavar="VALUE")
@click.pass_obj
def config_set(ctx: WorkstackContext, key: str, value: str) -> None:
    """Update configuration with a value for the given key."""
    # Parse key into parts
    parts = key.split(".")

    # Handle global config keys
    if parts[0] in ("workstacks_root", "use_graphite", "show_pr_info", "show_pr_checks"):
        if not ctx.global_config_ops.exists():
            click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}", err=True)
            click.echo("Run 'workstack init' to create it.", err=True)
            raise SystemExit(1)

        # Update value using set()
        if parts[0] == "workstacks_root":
            ctx.global_config_ops.set(workstacks_root=Path(value).expanduser().resolve())
        elif parts[0] == "use_graphite":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(use_graphite=value.lower() == "true")
        elif parts[0] == "show_pr_info":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(show_pr_info=value.lower() == "true")
        elif parts[0] == "show_pr_checks":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(show_pr_checks=value.lower() == "true")

        click.echo(f"Set {key}={value}")
        return

    # Handle rebase.* config keys
    if parts[0] == "rebase":
        if len(parts) != 2:
            click.echo(f"Invalid key: {key}", err=True)
            raise SystemExit(1)

        if not ctx.global_config_ops.exists():
            click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}", err=True)
            click.echo("Run 'workstack init' to create it.", err=True)
            raise SystemExit(1)

        # Validate and set rebase config
        subkey = parts[1]
        if subkey == "useStacks":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(rebase_use_stacks=value.lower() == "true")
        elif subkey == "autoTest":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(rebase_auto_test=value.lower() == "true")
        elif subkey == "preserveStacks":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(rebase_preserve_stacks=value.lower() == "true")
        elif subkey == "conflictTool":
            allowed_tools = ["vimdiff", "meld", "kdiff3", "opendiff", "code"]
            if value not in allowed_tools:
                click.echo(f"Invalid conflict tool: {value}", err=True)
                click.echo(f"Allowed tools: {', '.join(allowed_tools)}", err=True)
                raise SystemExit(1)
            ctx.global_config_ops.set(rebase_conflict_tool=value)
        elif subkey == "stackLocation":
            ctx.global_config_ops.set(rebase_stack_location=value)
        else:
            click.echo(f"Unknown rebase config key: {subkey}", err=True)
            click.echo(
                "Valid keys: useStacks, autoTest, preserveStacks, conflictTool, stackLocation",
                err=True,
            )
            raise SystemExit(1)

        click.echo(f"Set {key}={value}")
        return

    # Handle repo config keys - not implemented yet
    click.echo("Setting repo config keys not yet implemented", err=True)
    raise SystemExit(1)
