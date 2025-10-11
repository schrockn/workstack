"""Status information collectors."""

from workstack.status.collectors.base import StatusCollector
from workstack.status.collectors.git import GitStatusCollector

__all__ = [
    "StatusCollector",
    "GitStatusCollector",
]
