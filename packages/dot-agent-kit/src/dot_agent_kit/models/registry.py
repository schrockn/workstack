"""Registry models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistryEntry:
    """Kit entry in the registry."""

    kit_id: str
    name: str
    description: str
    source: str
    author: str | None = None
    tags: list[str] | None = None
