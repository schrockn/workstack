"""Registry models for dot-agent kit registry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistryEntry:
    """A single entry in the dot-agent registry."""

    name: str  # e.g., "gt-dot-agent-kit"
    url: str  # e.g., "https://github.com/dagsterlabs/gt-dot-agent-kit"
    description: str  # Brief description of the kit
    package_name: str  # Python package name (may differ from registry name)
    bundled: bool = False  # Whether the kit is bundled with dot-agent-kit

    def matches_search(self, term: str) -> bool:
        """Check if this entry matches a search term."""
        term_lower = term.lower()
        return (
            term_lower in self.name.lower()
            or term_lower in self.description.lower()
            or term_lower in self.package_name.lower()
        )


@dataclass(frozen=True)
class Registry:
    """The complete dot-agent kit registry."""

    entries: list[RegistryEntry]
    version: str  # Registry version

    def search(self, term: str) -> list[RegistryEntry]:
        """Search the registry for matching entries."""
        return [entry for entry in self.entries if entry.matches_search(term)]

    def find_by_name(self, name: str) -> RegistryEntry | None:
        """Find a specific entry by exact name match."""
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None
