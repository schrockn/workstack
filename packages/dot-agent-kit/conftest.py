from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()
