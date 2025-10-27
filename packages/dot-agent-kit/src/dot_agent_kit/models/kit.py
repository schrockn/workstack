"""Kit manifest models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KitManifest:
    """Kit manifest from kit.yaml."""

    name: str
    version: str
    description: str
    artifacts: dict[str, list[str]]  # type -> paths
    author: str | None = None
    license: str | None = None
    homepage: str | None = None
