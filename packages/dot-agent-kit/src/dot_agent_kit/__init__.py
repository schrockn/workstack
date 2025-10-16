"""Package initialization and version management."""

from importlib import metadata

PACKAGE_NAME = "dot-agent-kit"
DEFAULT_VERSION = "0.1.0"

# Exception handling acceptable here: metadata.version() provides no LBYL alternative.
# This catches cases where the package is run from source without being installed.
try:
    __version__ = metadata.version(PACKAGE_NAME)
except metadata.PackageNotFoundError:
    __version__ = DEFAULT_VERSION
