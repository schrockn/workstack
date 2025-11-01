"""Check command for validating artifacts."""

from pathlib import Path

import click

from dot_agent_kit.operations.validation import check_bundled_kits_sync, validate_project


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed validation information",
)
def check(verbose: bool) -> None:
    """Validate installed kit artifacts.

    This command performs two types of validation:
    1. Metadata validation - checks that all artifacts have valid frontmatter
    2. Sync validation - checks that bundled kit artifacts match their sources

    Exit codes:
      0 - All validations passed
      1 - One or more validations failed
    """
    project_dir = Path.cwd()

    # Phase 1: Metadata Validation
    click.echo("Metadata Validation")
    click.echo("===================")

    results = validate_project(project_dir)

    if len(results) == 0:
        click.echo("No artifacts found to validate")
        metadata_passed = True
    else:
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count

        # Show results
        if verbose or invalid_count > 0:
            for result in results:
                status = "✓" if result.is_valid else "✗"
                rel_path = result.artifact_path.relative_to(project_dir)
                click.echo(f"{status} {rel_path}")

                if not result.is_valid:
                    for error in result.errors:
                        click.echo(f"  - {error}", err=True)

        # Summary
        click.echo()
        click.echo(f"Validated {len(results)} artifacts:")
        click.echo(f"  ✓ Valid: {valid_count}")

        if invalid_count > 0:
            click.echo(f"  ✗ Invalid: {invalid_count}", err=True)
            metadata_passed = False
        else:
            click.echo("All artifacts are valid!")
            metadata_passed = True

    # Phase 2: Sync Validation (Bundled Kits)
    click.echo()
    click.echo("Sync Validation (Bundled Kits)")
    click.echo("==============================")

    sync_results = check_bundled_kits_sync(project_dir)

    if len(sync_results) == 0:
        click.echo("No bundled kits found to check")
        sync_passed = True
    else:
        total_artifacts = 0
        in_sync_count = 0
        out_of_sync_count = 0

        for kit_id, kit_results in sync_results:
            total_artifacts += len(kit_results)
            kit_in_sync = sum(1 for r in kit_results if r.is_in_sync)
            kit_out_of_sync = len(kit_results) - kit_in_sync

            in_sync_count += kit_in_sync
            out_of_sync_count += kit_out_of_sync

            if verbose or kit_out_of_sync > 0:
                click.echo(f"Kit: {kit_id}")
                for result in kit_results:
                    status = "✓" if result.is_in_sync else "✗"
                    rel_path = result.artifact_path.relative_to(project_dir)
                    click.echo(f"  {status} {rel_path}")

                    if not result.is_in_sync and result.reason is not None:
                        click.echo(f"      {result.reason}", err=True)

        # Summary
        click.echo()
        kits_summary = (
            f"Checked {total_artifacts} artifact(s) from {len(sync_results)} bundled kit(s):"
        )
        click.echo(kits_summary)
        click.echo(f"  ✓ In sync: {in_sync_count}")

        if out_of_sync_count > 0:
            click.echo(f"  ✗ Out of sync: {out_of_sync_count}", err=True)
            click.echo()
            sync_msg = "Run 'dot-agent sync' to update local artifacts from bundled sources"
            click.echo(sync_msg, err=True)
            sync_passed = False
        else:
            click.echo()
            click.echo("All bundled kit artifacts are in sync!")
            sync_passed = True

    # Overall result
    click.echo()
    if metadata_passed and sync_passed:
        click.echo("Overall Result: PASSED")
    else:
        failed_checks = []
        if not metadata_passed:
            failed_checks.append("metadata validation")
        if not sync_passed:
            failed_checks.append("sync validation")
        click.echo(f"Overall Result: FAILED ({', '.join(failed_checks)})", err=True)
        raise SystemExit(1)
