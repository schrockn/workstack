"""Kit manifest models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KitManifest:
    """Kit manifest from kit.yaml."""

    name: str
    version: str
    description: str
    artifacts: dict[str, list[str]]  # type -> paths
    license: str | None = None
    homepage: str | None = None

    def validate_namespace_pattern(self) -> list[str]:
        """Validate that artifacts follow required namespace pattern for kits.

        Returns a list of error messages for artifacts that don't follow the pattern:
        {type}s/{kit_name}/...

        Returns:
            List of error messages (empty if all artifacts follow the pattern)
        """
        warnings = []
        expected_namespace = self.name

        for artifact_type, paths in self.artifacts.items():
            type_prefix = f"{artifact_type}s"

            for artifact_path in paths:
                path_parts = Path(artifact_path).parts

                # Need at least 3 parts: type_prefix/namespace/file
                if len(path_parts) < 3:
                    warnings.append(
                        f"Artifact '{artifact_path}' is not namespaced (too shallow). "
                        f"Expected pattern: {type_prefix}/{expected_namespace}/..."
                    )
                    continue

                if path_parts[0] != type_prefix:
                    warnings.append(
                        f"Artifact '{artifact_path}' doesn't start with expected "
                        f"type prefix '{type_prefix}'. "
                        f"Expected pattern: {type_prefix}/{expected_namespace}/..."
                    )
                    continue

                if path_parts[1] != expected_namespace:
                    warnings.append(
                        f"Artifact '{artifact_path}' uses namespace '{path_parts[1]}' "
                        f"instead of kit name '{expected_namespace}'. "
                        f"Expected pattern: {type_prefix}/{expected_namespace}/..."
                    )

        return warnings
