"""Check command for verifying kit status."""

import click

from dot_agent_kit.io.state import load_project_config
from dot_agent_kit.operations.sync import check_kit_updates
from dot_agent_kit.operations.validation import (
    print_validation_results,
    validate_installed_artifacts,
)
from dot_agent_kit.utils.packaging import is_package_installed


@click.command()
@click.option("--validate", is_flag=True, help="Validate artifact frontmatter")
def check(validate: bool) -> None:
    """Check the status of installed kits."""
    config = load_project_config()

    if not config.kits:
        click.echo("No kits installed")
        return

    all_ok = True

    for kit in config.kits.values():
        # Check if package is still installed
        if not is_package_installed(kit.package_name):
            click.echo(f"✗ {kit.kit_id} - package not found: {kit.package_name}", err=True)
            all_ok = False
            continue

        # Check for updates
        new_version = check_kit_updates(kit)
        if new_version:
            click.echo(f"⚠ {kit.kit_id} v{kit.version} - update available: {new_version}")
            all_ok = False
        else:
            click.echo(f"✓ {kit.kit_id} v{kit.version} - synchronized")

    # Validate artifacts if requested
    if validate:
        click.echo("\nValidating artifacts...")
        validation_results = validate_installed_artifacts(config)
        print_validation_results(validation_results)
        if validation_results:
            all_ok = False

    if all_ok:
        click.echo("\n✓ All kits synchronized")
    else:
        click.echo("\n⚠ Some issues found. Run 'dot-agent sync' to update.")
        raise SystemExit(1)
