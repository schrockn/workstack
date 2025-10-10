"""Tests for PEP 723 script runner."""

from pathlib import Path

import pytest

from devclikit.exceptions import ScriptExecutionError
from devclikit.runner import run_pep723_script, validate_pep723_script


def test_run_pep723_script_success(tmp_path: Path) -> None:
    """Test successful script execution."""
    script = tmp_path / "script.py"
    script.write_text(
        """#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.13"
# ///
print("Hello from script")
""",
        encoding="utf-8",
    )

    result = run_pep723_script(script, capture_output=True)

    assert result.returncode == 0
    assert b"Hello from script" in result.stdout


def test_run_pep723_script_with_args(tmp_path: Path) -> None:
    """Test script execution with arguments."""
    script = tmp_path / "script.py"
    script.write_text(
        """#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.13"
# ///
import sys
print(f"Args: {sys.argv[1:]}")
""",
        encoding="utf-8",
    )

    result = run_pep723_script(script, args=["--test", "value"], capture_output=True)

    assert result.returncode == 0
    assert b"--test" in result.stdout
    assert b"value" in result.stdout


def test_run_pep723_script_file_not_found() -> None:
    """Test error when script file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        run_pep723_script(Path("/nonexistent/script.py"))


def test_run_pep723_script_execution_failure(tmp_path: Path) -> None:
    """Test error handling when script fails."""
    script = tmp_path / "script.py"
    script.write_text(
        """#!/usr/bin/env python3
# /// script
# dependencies = []
# requires-python = ">=3.13"
# ///
import sys
sys.exit(1)
""",
        encoding="utf-8",
    )

    with pytest.raises(ScriptExecutionError):
        run_pep723_script(script, check=True)


def test_validate_pep723_script_valid(tmp_path: Path) -> None:
    """Test validation of valid PEP 723 script."""
    script = tmp_path / "script.py"
    script.write_text(
        """#!/usr/bin/env python3
# /// script
# dependencies = ["click>=8.1.7"]
# requires-python = ">=3.13"
# ///
""",
        encoding="utf-8",
    )

    assert validate_pep723_script(script) is True


def test_validate_pep723_script_missing_marker(tmp_path: Path) -> None:
    """Test validation fails without PEP 723 marker."""
    script = tmp_path / "script.py"
    script.write_text("print('Hello')", encoding="utf-8")

    assert validate_pep723_script(script) is False


def test_validate_pep723_script_wrong_extension(tmp_path: Path) -> None:
    """Test validation fails for non-Python files."""
    script = tmp_path / "script.txt"
    script.write_text("# /// script\n# ///", encoding="utf-8")

    assert validate_pep723_script(script) is False


def test_validate_pep723_script_nonexistent() -> None:
    """Test validation fails for nonexistent files."""
    assert validate_pep723_script(Path("/nonexistent/script.py")) is False
