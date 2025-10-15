"""Branch metadata dataclass for Graphite integration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BranchMetadata:
    """Metadata for a single gt-tracked branch.

    This is used by the gt commands to provide machine-readable branch information.
    """

    name: str
    parent: str | None
    children: list[str]
    is_trunk: bool
    commit_sha: str
