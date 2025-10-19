"""Shared test fixtures and configuration."""

import json
import shutil
import tarfile
import tempfile
from pathlib import Path

import pytest


def load_fixture(fixture_path: str) -> str:
    """Load a fixture file as a string.

    Args:
        fixture_path: Path relative to tests/fixtures/ directory

    Returns:
        Content of the fixture file as a string
    """
    base_path = Path(__file__).parent / "fixtures" / fixture_path
    if not base_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return base_path.read_text(encoding="utf-8")


def load_json_fixture(fixture_path: str) -> dict:
    """Load a JSON fixture file.

    Args:
        fixture_path: Path relative to tests/fixtures/ directory

    Returns:
        Parsed JSON data as a dictionary
    """
    content = load_fixture(fixture_path)
    return json.loads(content)


@pytest.fixture
def extract_repo_fixture():
    """Fixture that extracts tarred git repositories for testing.

    Returns a function that extracts a repo and returns its path.
    The extracted repo is automatically cleaned up after the test.
    """
    temp_dirs = []

    def extract(fixture_name: str) -> Path:
        """Extract a repository fixture.

        Args:
            fixture_name: Name of the fixture (without .tar.gz extension)

        Returns:
            Path to the extracted repository
        """
        fixture_path = Path(__file__).parent / "fixtures" / "repos" / f"{fixture_name}.tar.gz"
        if not fixture_path.exists():
            raise FileNotFoundError(f"Repository fixture not found: {fixture_name}")

        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp(prefix="test_repo_")
        temp_dirs.append(temp_dir)

        # Extract the tarball
        with tarfile.open(fixture_path, "r:gz") as tar:
            tar.extractall(temp_dir)

        # Return the path to the extracted repo
        # Assume the tarball contains a single directory at the root
        extracted_items = list(Path(temp_dir).iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            return extracted_items[0]
        return Path(temp_dir)

    yield extract

    # Cleanup all temporary directories
    for temp_dir in temp_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing.

    Yields:
        Path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="test_workspace_")
    yield Path(temp_dir)
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
