"""Validation operations for installed artifacts."""

from pathlib import Path

import click

from dot_agent_kit.io.frontmatter import load_artifact
from dot_agent_kit.models.config import ProjectConfig


def validate_installed_artifacts(config: ProjectConfig) -> dict[str, list[str]]:
    """Validate all installed artifacts."""
    validation_results = {}
    root_dir = Path(config.root_dir)

    for kit in config.kits.values():
        errors = []

        for artifact_path in kit.artifacts:
            full_path = root_dir / artifact_path

            if not full_path.exists():
                errors.append(f"Missing artifact: {artifact_path}")
                continue

            artifact = load_artifact(full_path)
            if not artifact.is_valid:
                for error in artifact.validation_errors:
                    errors.append(f"{artifact_path}: {error}")

        if errors:
            validation_results[kit.kit_id] = errors

    return validation_results


def print_validation_results(results: dict[str, list[str]]) -> None:
    """Print validation results to the console."""
    if not results:
        click.echo("✓ All artifacts validated successfully")
        return

    click.echo("Validation errors found:", err=True)
    for kit_id, errors in results.items():
        click.echo(f"\n{kit_id}:", err=True)
        for error in errors:
            click.echo(f"  ✗ {error}", err=True)
