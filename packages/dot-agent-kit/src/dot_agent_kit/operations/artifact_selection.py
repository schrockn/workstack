"""Artifact selection and filtering operations."""

from pathlib import Path

from dot_agent_kit.models import KitManifest


class ArtifactSpec:
    """Specification for artifact selection.

    Parses kit:artifact1,artifact2 syntax to select specific artifacts from a kit.
    """

    def __init__(self, spec_string: str):
        """Parse kit:artifact1,artifact2 syntax.

        Args:
            spec_string: Spec in format "kit-id" or "kit-id:artifact1,artifact2"

        Examples:
            "github-workflows" - all artifacts from github-workflows kit
            "github-workflows:pr-review" - just pr-review artifact
            "github-workflows:pr-review,auto-merge" - pr-review and auto-merge artifacts
        """
        self.spec_string = spec_string

        # Parse kit ID and artifact names
        if ":" in spec_string:
            kit_id, artifacts_str = spec_string.split(":", 1)
            self.kit_id = kit_id.strip()
            # Split by comma and strip whitespace
            self.artifact_names = [
                name.strip() for name in artifacts_str.split(",") if name.strip()
            ]
        else:
            self.kit_id = spec_string.strip()
            self.artifact_names = []

    def get_kit_id(self) -> str:
        """Get the kit identifier."""
        return self.kit_id

    def get_artifact_names(self) -> list[str] | None:
        """Get selected artifact names, or None for all artifacts."""
        if not self.artifact_names:
            return None
        return self.artifact_names

    def filter_artifacts(self, manifest: KitManifest) -> dict[str, list[str]]:
        """Filter manifest artifacts based on selection.

        Args:
            manifest: Kit manifest with all artifacts

        Returns:
            Filtered artifacts dict (type -> paths)

        Raises:
            ValueError: If selected artifact names are not found in manifest
        """
        # If no specific artifacts selected, return all
        if not self.artifact_names:
            return manifest.artifacts

        # Build set of selected artifact names for faster lookup
        selected_names = set(self.artifact_names)
        found_names: set[str] = set()

        # Filter artifacts by name
        filtered: dict[str, list[str]] = {}
        for artifact_type, paths in manifest.artifacts.items():
            filtered_paths: list[str] = []
            for path in paths:
                # Extract artifact name from path (filename without extension)
                artifact_name = Path(path).stem
                if artifact_name in selected_names:
                    filtered_paths.append(path)
                    found_names.add(artifact_name)

            if filtered_paths:
                filtered[artifact_type] = filtered_paths

        # Check if all selected artifacts were found
        missing_names = selected_names - found_names
        if missing_names:
            missing_str = ", ".join(sorted(missing_names))
            raise ValueError(
                f"Artifacts not found in kit '{self.kit_id}': {missing_str}\n"
                f"Available artifacts: {', '.join(sorted(self._get_all_artifact_names(manifest)))}"
            )

        return filtered

    def _get_all_artifact_names(self, manifest: KitManifest) -> list[str]:
        """Get all artifact names from manifest (for error messages)."""
        names: list[str] = []
        for paths in manifest.artifacts.values():
            for path in paths:
                names.append(Path(path).stem)
        return names
