"""Conflict resolution for rebase stacks."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import click

from workstack.core.gitops import GitOps
from workstack.core.rebase_utils import parse_conflict_markers


@dataclass(frozen=True)
class Resolution:
    """Represents a conflict resolution choice."""

    file_path: str
    strategy: str  # "ours", "theirs", "manual"
    resolved_content: str | None  # For manual resolutions


class ConflictResolver:
    """Interactive conflict resolution for rebase stacks."""

    def __init__(self, git_ops: GitOps) -> None:
        """Initialize the conflict resolver.

        Args:
            git_ops: GitOps instance for git operations
        """
        self.git_ops = git_ops

    def resolve_interactively(
        self,
        stack_path: Path,
        conflicts: list[str],
    ) -> list[Resolution]:
        """Resolve conflicts interactively.

        Args:
            stack_path: Path to rebase stack
            conflicts: List of conflicted file paths

        Returns:
            List of resolutions applied
        """
        resolutions = []

        for file_path in conflicts:
            full_path = stack_path / file_path
            content = full_path.read_text(encoding="utf-8")

            conflict_info = parse_conflict_markers(content)

            click.echo(f"\nConflict in: {click.style(file_path, fg='cyan', bold=True)}")
            click.echo(f"Number of conflict regions: {len(conflict_info)}")

            choice = self._prompt_resolution_strategy(file_path)

            if choice == "ours":
                resolved = self._resolve_keep_ours(content)
                resolutions.append(Resolution(file_path, "ours", resolved))
            elif choice == "theirs":
                resolved = self._resolve_keep_theirs(content)
                resolutions.append(Resolution(file_path, "theirs", resolved))
            elif choice == "manual":
                self._open_in_editor(full_path)
                # Verify resolution
                if self._check_resolution_complete(full_path):
                    resolutions.append(Resolution(file_path, "manual", None))
                else:
                    click.echo("  Warning: Conflict markers still present", err=True)

        return resolutions

    def apply_resolution(
        self,
        stack_path: Path,
        resolution: Resolution,
    ) -> None:
        """Apply a resolution to a file.

        Args:
            stack_path: Path to the stack
            resolution: Resolution to apply
        """
        if resolution.resolved_content is not None:
            file_path = stack_path / resolution.file_path
            file_path.write_text(resolution.resolved_content, encoding="utf-8")

        # Stage the resolved file
        subprocess.run(
            ["git", "add", resolution.file_path],
            cwd=stack_path,
            check=True,
            capture_output=True,
        )

    def _prompt_resolution_strategy(self, file_path: str) -> str:
        """Prompt user for resolution strategy.

        Args:
            file_path: Path to the conflicted file

        Returns:
            Strategy choice: "ours", "theirs", "manual", or "skip"
        """
        click.echo("\nResolution options:")
        click.echo("  1. Keep ours (discard their changes)")
        click.echo("  2. Keep theirs (discard our changes)")
        click.echo("  3. Manual (open in editor)")
        click.echo("  4. Skip for now")

        choice = click.prompt(
            "Choose resolution strategy",
            type=click.Choice(["1", "2", "3", "4"]),
            default="3",
        )

        mapping = {"1": "ours", "2": "theirs", "3": "manual", "4": "skip"}
        return mapping[choice]

    def _resolve_keep_ours(self, content: str) -> str:
        """Resolve by keeping 'ours' version.

        Args:
            content: File content with conflict markers

        Returns:
            Resolved content with 'ours' version kept
        """
        lines = content.split("\n")
        result = []
        in_conflict = False
        in_ours = False

        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
                in_ours = True
                continue
            elif line.startswith("======="):
                in_ours = False
                continue
            elif line.startswith(">>>>>>>"):
                in_conflict = False
                in_ours = False
                continue

            if not in_conflict:
                result.append(line)
            elif in_ours:
                result.append(line)

        return "\n".join(result)

    def _resolve_keep_theirs(self, content: str) -> str:
        """Resolve by keeping 'theirs' version.

        Args:
            content: File content with conflict markers

        Returns:
            Resolved content with 'theirs' version kept
        """
        lines = content.split("\n")
        result = []
        in_conflict = False
        in_theirs = False

        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
                continue
            elif line.startswith("======="):
                in_theirs = True
                continue
            elif line.startswith(">>>>>>>"):
                in_conflict = False
                in_theirs = False
                continue

            if not in_conflict:
                result.append(line)
            elif in_theirs:
                result.append(line)

        return "\n".join(result)

    def _open_in_editor(self, file_path: Path) -> None:
        """Open file in configured editor.

        Args:
            file_path: Path to file to open
        """
        editor = os.environ.get("EDITOR", "vim")

        try:
            subprocess.run([editor, str(file_path)], check=True)
        except subprocess.CalledProcessError:
            click.echo(f"  Error opening editor: {editor}", err=True)

    def _check_resolution_complete(self, file_path: Path) -> bool:
        """Check if all conflict markers are resolved.

        Args:
            file_path: Path to file to check

        Returns:
            True if no conflict markers remain
        """
        content = file_path.read_text(encoding="utf-8")
        markers = ["<<<<<<<", "=======", ">>>>>>>"]
        return not any(marker in content for marker in markers)
