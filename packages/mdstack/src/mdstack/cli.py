import logging
from pathlib import Path

import click
import yaml

from mdstack.discovery import discover_scopes, find_scope_and_descendants, find_scope_by_path
from mdstack.llm.config import create_llm_client, load_config
from mdstack.manifest import is_stale
from mdstack.propagation import generate_bottom_up
from mdstack.validation import TamperDetectionError, check_all_scopes

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, verbose):
    """mdstack - Hierarchical documentation generator"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(message)s")
    # Store verbose flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--model", help="LLM model to use", default="claude-3-5-sonnet-20241022")
def init(model):
    """Initialize mdstack in repository."""
    from mdstack.package_detection import detect_package_root, discover_python_packages

    click.echo(click.style("🚀 Initializing mdstack...", fg="cyan", bold=True))

    # Discover existing scopes
    scopes = discover_scopes()

    # Find package roots and create CLAUDE.md for Python subpackages
    existing_claude_paths = {scope.path for scope in scopes}
    packages_created = []

    # Check if current directory or any scope is a package root
    all_potential_roots = [Path.cwd()] + [scope.path for scope in scopes]

    for potential_root in all_potential_roots:
        package_layout = detect_package_root(potential_root)

        if not package_layout:
            continue

        # Discover Python packages in each source directory
        for source_dir in package_layout.source_dirs:
            python_packages = discover_python_packages(source_dir)

            for package_path in python_packages:
                # Skip if CLAUDE.md already exists
                if package_path in existing_claude_paths:
                    continue

                # Create CLAUDE.md for this package
                claude_md_path = package_path / "CLAUDE.md"
                if not claude_md_path.exists():
                    # Create minimal CLAUDE.md
                    package_name = package_path.name
                    content = f"# {package_name}\n\n"
                    claude_md_path.write_text(content, encoding="utf-8")
                    packages_created.append(package_path)

    # Re-discover scopes after creating CLAUDE.md files
    scopes = discover_scopes()
    count_style = click.style(str(len(scopes)), fg="green", bold=True)
    click.echo(f"Found {count_style} scopes with CLAUDE.md:")
    for scope in scopes:
        click.echo(f"  • {click.style(str(scope.path), fg='blue')}")

    if packages_created:
        created_count = click.style(str(len(packages_created)), fg="green", bold=True)
        click.echo(f"\nCreated CLAUDE.md for {created_count} Python packages:")
        for pkg_path in packages_created:
            click.echo(f"  • {click.style(str(pkg_path), fg='green')}")

    # Create .mdstack directories
    for scope in scopes:
        scope.mdstack_dir.mkdir(parents=True, exist_ok=True)

    # Create config file
    config_path = Path.cwd() / ".mdstack.config.yaml"

    if config_path.exists():
        path_style = click.style(str(config_path), fg="yellow")
        click.echo(f"\nConfig file already exists: {path_style}")
    else:
        config = {
            "llm": {
                "provider": "anthropic",
                "model": model,
                "api_key_env": "ANTHROPIC_API_KEY",
                "max_tokens": 4000,
                "temperature": 0.1,
            }
        }

        config_path.write_text(yaml.dump(config, default_flow_style=False))
        path_style = click.style(str(config_path), fg="green")
        click.echo(f"\nCreated config file: {path_style}")
        click.echo(f"Provider: {click.style('anthropic', fg='cyan')}")
        click.echo(f"Model: {click.style(model, fg='cyan')}")
        api_key_style = click.style("ANTHROPIC_API_KEY", fg="yellow", bold=True)
        click.echo(f"\nSet environment variable: {api_key_style}")

    click.echo(click.style("\n✅ Initialization complete", fg="green", bold=True))
    click.echo("\nNext steps:")
    click.echo("  1. Set your ANTHROPIC_API_KEY environment variable")
    click.echo(f"  2. Run: {click.style('mdstack generate', fg='cyan', bold=True)}")


@cli.command()
@click.argument("scope_path", required=False, type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Preview what would be generated")
@click.option("--no-cache", is_flag=True, help="Disable prompt caching")
@click.pass_context
def generate(ctx, scope_path, dry_run, no_cache):
    """Generate .mdstack/ documentation."""
    from mdstack.package_detection import detect_package_root, discover_python_packages

    if dry_run:
        click.echo(click.style("🔍 DRY RUN - No files will be written\n", fg="yellow", bold=True))

    # Auto-discover and create CLAUDE.md for Python subpackages
    scopes = discover_scopes()
    existing_claude_paths = {scope.path for scope in scopes}
    packages_created = []

    # Check if current directory or any scope is a package root
    all_potential_roots = [Path.cwd()] + [scope.path for scope in scopes]

    for potential_root in all_potential_roots:
        package_layout = detect_package_root(potential_root)

        if not package_layout:
            continue

        # Discover Python packages in each source directory
        for source_dir in package_layout.source_dirs:
            python_packages = discover_python_packages(source_dir)

            for package_path in python_packages:
                # Skip if CLAUDE.md already exists
                if package_path in existing_claude_paths:
                    continue

                # Create CLAUDE.md for this package
                claude_md_path = package_path / "CLAUDE.md"
                if not claude_md_path.exists():
                    # Create minimal CLAUDE.md
                    package_name = package_path.name
                    content = f"# {package_name}\n\n"
                    claude_md_path.write_text(content, encoding="utf-8")
                    packages_created.append(package_path)

    if packages_created:
        created_count = click.style(str(len(packages_created)), fg="green", bold=True)
        click.echo(f"Created CLAUDE.md for {created_count} Python packages:")
        for pkg_path in packages_created:
            click.echo(f"  • {click.style(str(pkg_path), fg='green')}")
        click.echo()

    # Load configuration
    try:
        config = load_config()
        # Add verbose flag from CLI context
        verbose = ctx.obj.get("verbose", False)
        config.verbose = verbose
        # Override caching if --no-cache flag is set
        if no_cache:
            config.enable_caching = False
    except ValueError as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red", bold=True), err=True)
        msg = "\nRun 'mdstack init' to create configuration"
        click.echo(click.style(msg, fg="yellow"), err=True)
        raise SystemExit(1) from None

    # Display configuration
    provider_style = click.style(config.provider, fg="cyan")
    click.echo(f"Using {provider_style} with models:")
    for file_type, model in config.models.items():
        model_style = click.style(model, fg="cyan")
        click.echo(f"  • {file_type}: {model_style}")
    click.echo()

    # Create a default LLM client (for backward compatibility, though it won't be used
    # when config is provided since propagation.py creates specialized clients)
    llm_client = create_llm_client(config, "architecture")

    # Re-discover scopes after potentially creating new CLAUDE.md files
    all_scopes = discover_scopes()

    if scope_path:
        # Generate for specific scope and its descendants (bottom-up)
        scope = find_scope_by_path(scope_path, all_scopes)
        if not scope:
            msg = f"❌ Error: No scope found for path {scope_path}"
            click.echo(click.style(msg, fg="red"), err=True)
            raise SystemExit(1) from None

        # Find all scopes under the specified scope (including itself)
        scopes_to_generate = find_scope_and_descendants(scope, all_scopes)
        count_style = click.style(str(len(scopes_to_generate)), fg="green", bold=True)
        path_style = click.style(str(scope.path), fg="blue")
        click.echo(f"Generating for {count_style} scope(s) under: {path_style}\n")

        if dry_run:
            # Show scopes in generation order (deepest first)
            scopes_by_depth = sorted(
                scopes_to_generate, key=lambda s: len(s.path.parts), reverse=True
            )
            for s in scopes_by_depth:
                click.echo(f"Would generate: {click.style(str(s.path), fg='blue')}")
            return

        try:
            generate_bottom_up(scopes_to_generate, llm_client, config)
        except TamperDetectionError as e:
            click.echo(click.style(f"\n❌ {e}", fg="red", bold=True), err=True)
            raise SystemExit(1) from None
        except Exception as e:
            msg = f"\n❌ Error during generation: {e}"
            click.echo(click.style(msg, fg="red"), err=True)
            raise SystemExit(1) from None
    else:
        # Generate for all scopes - use bottom-up generation
        count_style = click.style(str(len(all_scopes)), fg="green", bold=True)
        click.echo(f"Generating for {count_style} scopes (bottom-up)\n")

        if dry_run:
            # Show scopes in generation order (deepest first)
            scopes_by_depth = sorted(all_scopes, key=lambda s: len(s.path.parts), reverse=True)
            for scope in scopes_by_depth:
                click.echo(f"Would generate: {click.style(str(scope.path), fg='blue')}")
            return

        try:
            generate_bottom_up(all_scopes, llm_client, config)
        except TamperDetectionError as e:
            click.echo(click.style(f"\n❌ {e}", fg="red", bold=True), err=True)
            raise SystemExit(1) from None
        except Exception as e:
            msg = f"\n❌ Error during generation: {e}"
            click.echo(click.style(msg, fg="red"), err=True)
            raise SystemExit(1) from None

    click.echo(click.style("\n🎉 Generation complete", fg="green", bold=True))


@cli.command()
@click.option("--strict", is_flag=True, help="Exit with error if any stale")
def check(strict):
    """Verify .mdstack/ folders are up-to-date and not manually edited."""
    scopes = discover_scopes()

    # Check for tampering
    click.echo(click.style("🔍 Checking for manual edits...", fg="blue"))
    tampered = check_all_scopes(scopes)

    if tampered:
        click.echo(click.style("\n❌ Manual edits detected:\n", fg="red", bold=True), err=True)
        for scope, error in tampered:
            click.echo(click.style(f"  • {scope.path}", fg="red"), err=True)
            click.echo(f"    {error}", err=True)
        msg = "\nRevert manual changes or run 'mdstack generate' to regenerate."
        click.echo(click.style(msg, fg="yellow"), err=True)
        raise SystemExit(1) from None

    click.echo(click.style("✅ No manual edits detected\n", fg="green"))

    # Check for staleness
    click.echo(click.style("🔍 Checking for stale documentation...", fg="blue"))
    stale_scopes = []
    fresh_scopes = []

    for scope in scopes:
        if is_stale(scope):
            stale_scopes.append(scope)
        else:
            fresh_scopes.append(scope)

    click.echo(f"Checked {click.style(str(len(scopes)), fg='cyan', bold=True)} scopes:")
    fresh_label = click.style("✅ Fresh:", fg="green")
    fresh_count = click.style(str(len(fresh_scopes)), fg="green", bold=True)
    click.echo(f"  {fresh_label} {fresh_count}")
    stale_label = click.style("⚠️  Stale:", fg="yellow")
    stale_count = click.style(str(len(stale_scopes)), fg="yellow", bold=True)
    click.echo(f"  {stale_label} {stale_count}")

    if stale_scopes:
        msg = "\n⚠️  Stale scopes (need regeneration):"
        click.echo(click.style(msg, fg="yellow", bold=True))
        for scope in stale_scopes:
            click.echo(f"  • {click.style(str(scope.path), fg='yellow')}")

        click.echo("\nTo fix, run:")
        click.echo(f"  {click.style('mdstack generate', fg='cyan', bold=True)}")

        if strict:
            raise SystemExit(1)


@cli.command()
@click.argument("query")
def lookup(query):
    """Search LOOKUP.md files for query."""
    scopes = discover_scopes()

    query_lower = query.lower()
    results = []

    for scope in scopes:
        lookup_file = scope.mdstack_dir / "LOOKUP.md"
        if not lookup_file.exists():
            continue

        content = lookup_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # Get context (surrounding lines)
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])

                results.append((scope, i, context))

    if not results:
        click.echo(click.style(f"❌ No results found for: {query}", fg="yellow"))
        return

    click.echo(click.style(f"🔍 Found {len(results)} matches:\n", fg="green", bold=True))

    for scope, line_num, context in results:
        click.echo(click.style(f"=== {scope.path} (line {line_num}) ===", fg="cyan", bold=True))
        click.echo(context)
        click.echo()


@cli.command()
@click.argument("scope_path", required=False, type=click.Path(exists=True, path_type=Path))
def rehash(scope_path):
    """Recompute hashes for .mdstack/ files and update manifests."""
    from mdstack.hashing import compute_combined_hash, compute_hash
    from mdstack.manifest import load_manifest, save_manifest
    from mdstack.models import Manifest

    click.echo(click.style("🔄 Recomputing hashes...", fg="cyan", bold=True))

    # Discover scopes
    all_scopes = discover_scopes()

    if scope_path:
        # Rehash specific scope only
        scope = find_scope_by_path(scope_path, all_scopes)
        if not scope:
            msg = f"❌ Error: No scope found for path {scope_path}"
            click.echo(click.style(msg, fg="red"), err=True)
            raise SystemExit(1) from None
        scopes_to_rehash = [scope]
        path_style = click.style(str(scope.path), fg="blue")
        click.echo(f"Rehashing scope: {path_style}\n")
    else:
        # Rehash all scopes
        scopes_to_rehash = all_scopes
        count_style = click.style(str(len(all_scopes)), fg="green", bold=True)
        click.echo(f"Rehashing {count_style} scopes\n")

    rehashed_count = 0
    skipped_count = 0

    for scope in scopes_to_rehash:
        manifest = load_manifest(scope)

        if not manifest:
            click.echo(click.style(f"⚠️  Skipping {scope.path} (no manifest)", fg="yellow"))
            skipped_count += 1
            continue

        # Compute hashes for each file
        tests_hash = ""
        lookup_hash = ""
        architecture_hash = ""

        tests_file = scope.mdstack_dir / "TESTS.md"
        if tests_file.exists():
            tests_content = tests_file.read_text(encoding="utf-8")
            tests_hash = compute_hash(tests_content)

        lookup_file = scope.mdstack_dir / "LOOKUP.md"
        if lookup_file.exists():
            lookup_content = lookup_file.read_text(encoding="utf-8")
            lookup_hash = compute_hash(lookup_content)

        architecture_file = scope.mdstack_dir / "OBSERVED_ARCHITECTURE.md"
        if architecture_file.exists():
            architecture_content = architecture_file.read_text(encoding="utf-8")
            architecture_hash = compute_hash(architecture_content)

        # Compute combined hash
        content_hash = compute_combined_hash(tests_hash, lookup_hash, architecture_hash)

        # Create updated manifest
        updated_manifest = Manifest.create(
            content_hash=content_hash,
            llm_provider=manifest.llm_provider,
            llm_model=manifest.llm_model,
            generator_version=manifest.generator_version,
            tests_hash=tests_hash,
            lookup_hash=lookup_hash,
            architecture_hash=architecture_hash,
            generated_at=manifest.generated_at,  # Keep original timestamp
        )

        # Save updated manifest
        save_manifest(scope, updated_manifest)

        click.echo(click.style(f"✅ Rehashed {scope.path}", fg="green"))
        rehashed_count += 1

    click.echo()
    click.echo(click.style("🎉 Rehashing complete", fg="green", bold=True))
    click.echo(f"Rehashed: {click.style(str(rehashed_count), fg='green', bold=True)}")
    if skipped_count > 0:
        click.echo(f"Skipped: {click.style(str(skipped_count), fg='yellow', bold=True)}")


if __name__ == "__main__":
    cli()
