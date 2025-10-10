"""Tests for utility functions."""

from pathlib import Path

from devclikit.utils import ensure_directory, is_valid_command_name


def test_ensure_directory_creates_directory(tmp_path: Path) -> None:
    """Test that ensure_directory creates a directory."""
    new_dir = tmp_path / "new_directory"

    ensure_directory(new_dir)

    assert new_dir.exists()
    assert new_dir.is_dir()


def test_ensure_directory_creates_nested_directories(tmp_path: Path) -> None:
    """Test that ensure_directory creates nested directories."""
    nested_dir = tmp_path / "level1" / "level2" / "level3"

    ensure_directory(nested_dir)

    assert nested_dir.exists()
    assert nested_dir.is_dir()


def test_ensure_directory_does_nothing_if_exists(tmp_path: Path) -> None:
    """Test that ensure_directory is idempotent."""
    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()

    # Should not raise
    ensure_directory(existing_dir)

    assert existing_dir.exists()


def test_is_valid_command_name_accepts_lowercase() -> None:
    """Test that lowercase names are valid."""
    assert is_valid_command_name("test") is True
    assert is_valid_command_name("mycommand") is True


def test_is_valid_command_name_accepts_hyphens() -> None:
    """Test that hyphenated names are valid."""
    assert is_valid_command_name("test-command") is True
    assert is_valid_command_name("my-test-command") is True


def test_is_valid_command_name_accepts_numbers() -> None:
    """Test that names with numbers are valid."""
    assert is_valid_command_name("test123") is True
    assert is_valid_command_name("test-123") is True


def test_is_valid_command_name_rejects_uppercase() -> None:
    """Test that uppercase letters are invalid."""
    assert is_valid_command_name("Test") is False
    assert is_valid_command_name("TEST") is False


def test_is_valid_command_name_rejects_special_chars() -> None:
    """Test that special characters are invalid."""
    assert is_valid_command_name("test_command") is False
    assert is_valid_command_name("test.command") is False
    assert is_valid_command_name("test@command") is False


def test_is_valid_command_name_rejects_leading_hyphen() -> None:
    """Test that leading hyphens are invalid."""
    assert is_valid_command_name("-test") is False


def test_is_valid_command_name_rejects_trailing_hyphen() -> None:
    """Test that trailing hyphens are invalid."""
    assert is_valid_command_name("test-") is False


def test_is_valid_command_name_rejects_empty() -> None:
    """Test that empty string is invalid."""
    assert is_valid_command_name("") is False
