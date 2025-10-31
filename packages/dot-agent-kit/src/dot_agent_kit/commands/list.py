"""List command for showing installed artifacts."""

from pathlib import Path

import click

from dot_agent_kit.io import (
    create_default_config,
    load_project_config,
)
from dot_agent_kit.models.artifact import ArtifactSource, InstalledArtifact
from dot_agent_kit.models.config import ProjectConfig
from dot_agent_kit.repositories import ArtifactRepository, FilesystemArtifactRepository


def _format_source(artifact: InstalledArtifact) -> str:
    """Format the source attribution string for an artifact.

    Args:
        artifact: The artifact to format

    Returns:
        Formatted source string like "[devrun@0.1.0]" or "[local]"
    """
    if artifact.source == ArtifactSource.LOCAL:
        return "[local]"
    elif artifact.kit_id and artifact.kit_version:
        return f"[{artifact.kit_id}@{artifact.kit_version}]"
    elif artifact.kit_id:
        return f"[{artifact.kit_id}]"
    else:
        return "[unknown]"


def _list_artifacts(
    config: ProjectConfig,
    project_dir: Path,
    repository: ArtifactRepository,
) -> None:
    """List all installed artifacts in artifact-focused format.

    Args:
        config: Project configuration
        project_dir: Project directory for artifact discovery
        repository: Repository for artifact discovery
    """
    # Discover all artifacts using the provided repository
    artifacts = repository.discover_all_artifacts(project_dir, config)

    if not artifacts:
        click.echo("No artifacts installed")
        return

    # Group artifacts by type
    skills: list[InstalledArtifact] = []
    commands: list[InstalledArtifact] = []
    agents: list[InstalledArtifact] = []

    for artifact in artifacts:
        if artifact.artifact_type == "skill":
            skills.append(artifact)
        elif artifact.artifact_type == "command":
            commands.append(artifact)
        elif artifact.artifact_type == "agent":
            agents.append(artifact)

    # Calculate column widths for alignment
    max_name_len = 0
    max_source_len = 0

    for artifact in artifacts:
        max_name_len = max(max_name_len, len(artifact.artifact_name))
        max_source_len = max(max_source_len, len(_format_source(artifact)))

    # Ensure minimum widths
    max_name_len = max(max_name_len, 20)
    max_source_len = max(max_source_len, 20)

    # Display skills
    if skills:
        click.echo("Skills:")
        for skill in sorted(skills, key=lambda a: a.artifact_name):
            name = skill.artifact_name.ljust(max_name_len)
            source = _format_source(skill).ljust(max_source_len)
            path = str(skill.file_path)
            click.echo(f"  {name} {source} {path}")
        click.echo()

    # Display commands
    if commands:
        click.echo("Commands:")
        for command in sorted(commands, key=lambda a: a.artifact_name):
            name = command.artifact_name.ljust(max_name_len)
            source = _format_source(command).ljust(max_source_len)
            path = str(command.file_path)
            click.echo(f"  {name} {source} {path}")
        click.echo()

    # Display agents
    if agents:
        click.echo("Agents:")
        for agent in sorted(agents, key=lambda a: a.artifact_name):
            name = agent.artifact_name.ljust(max_name_len)
            source = _format_source(agent).ljust(max_source_len)
            path = str(agent.file_path)
            click.echo(f"  {name} {source} {path}")


@click.command("list")
def list_cmd() -> None:
    """List all installed artifacts."""
    # Load project config
    project_dir = Path.cwd()
    loaded_config = load_project_config(project_dir)
    config = loaded_config if loaded_config is not None else create_default_config()

    # Create filesystem repository for production use
    repository = FilesystemArtifactRepository()
    _list_artifacts(config, project_dir, repository)


@click.command("ls", hidden=True)
def ls_cmd() -> None:
    """List all installed artifacts."""
    # Load project config
    project_dir = Path.cwd()
    loaded_config = load_project_config(project_dir)
    config = loaded_config if loaded_config is not None else create_default_config()

    # Create filesystem repository for production use
    repository = FilesystemArtifactRepository()
    _list_artifacts(config, project_dir, repository)
