"""Error handling and edge case tests for global config operations.

This test module focuses on I/O errors, corruption scenarios, and edge cases
that are critical for configuration reliability.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from workstack.core.global_config_ops import RealGlobalConfigOps


class TestGlobalConfigIOErrors:
    """Test I/O error handling in global config operations."""

    def test_config_read_with_permission_denied(self, tmp_path: Path) -> None:
        """Test config handling when file is not readable."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """workstacks_root = "/home/test"
use_graphite = true
""",
            encoding="utf-8",
        )

        # Make file unreadable
        os.chmod(config_path, 0o000)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        try:
            with pytest.raises(PermissionError):
                config_ops.get_workstacks_root()
        finally:
            # Restore permissions for cleanup
            os.chmod(config_path, 0o644)

    def test_config_read_with_corrupted_file(self, tmp_path: Path) -> None:
        """Test config handling with corrupted TOML."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """[this is not valid TOML
workstacks_root = unclosed string"
use_graphite = not a boolean
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Should raise when trying to parse invalid TOML
        import tomllib

        with pytest.raises(tomllib.TOMLDecodeError):
            config_ops.get_workstacks_root()

    def test_config_read_with_invalid_json_style(self, tmp_path: Path) -> None:
        """Test config handling when someone writes JSON instead of TOML."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        # Common mistake: writing JSON instead of TOML
        config_path.write_text(
            """{
    "workstacks_root": "/home/test",
    "use_graphite": true
}""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Should fail to parse JSON as TOML
        import tomllib

        with pytest.raises(tomllib.TOMLDecodeError):
            config_ops.get_workstacks_root()

    def test_config_write_with_disk_full(self, tmp_path: Path) -> None:
        """Test config write when disk is full."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        with patch.object(Path, "write_text") as mock_write:
            mock_write.side_effect = OSError(28, "No space left on device")

            with pytest.raises(OSError) as exc_info:
                config_ops.set(workstacks_root=Path("/test"))

            assert exc_info.value.errno == 28

    def test_config_write_with_readonly_filesystem(self, tmp_path: Path) -> None:
        """Test config write on read-only filesystem."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Make parent directory read-only
        os.chmod(config_path.parent, 0o444)

        try:
            with pytest.raises(PermissionError):
                config_ops.set(workstacks_root=Path("/test"))
        finally:
            # Restore permissions
            os.chmod(config_path.parent, 0o755)

    def test_config_directory_not_exists(self, tmp_path: Path) -> None:
        """Test that set() creates directory if it doesn't exist."""
        config_path = tmp_path / "new_dir" / ".workstack" / "config.toml"
        assert not config_path.parent.exists()

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        config_ops.set(workstacks_root=Path("/test"))

        assert config_path.exists()
        assert config_path.parent.is_dir()

    def test_config_with_symlink_directory(self, tmp_path: Path) -> None:
        """Test config operations with symlinked config directory."""
        real_dir = tmp_path / "real_config"
        symlink_dir = tmp_path / ".workstack"
        real_dir.mkdir()
        symlink_dir.symlink_to(real_dir)

        config_path = symlink_dir / "config.toml"
        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        config_ops.set(workstacks_root=Path("/test"))

        # Should write through symlink
        assert (real_dir / "config.toml").exists()
        assert config_path.exists()
        assert config_ops.get_workstacks_root() == Path("/test")

    def test_config_cache_invalidation_after_write(self, tmp_path: Path) -> None:
        """Test that cache is properly invalidated after writes."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Initial write
        config_ops.set(workstacks_root=Path("/initial"))
        assert config_ops.get_workstacks_root() == Path("/initial")

        # Update
        config_ops.set(workstacks_root=Path("/updated"))
        assert config_ops.get_workstacks_root() == Path("/updated")

        # Cache should reflect new value
        assert config_ops._cache is None or config_ops._cache["workstacks_root"] == Path("/updated")

    def test_config_concurrent_modification(self, tmp_path: Path) -> None:
        """Test config behavior when file is modified externally."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Initial write
        config_ops.set(workstacks_root=Path("/initial"))

        # Cache the value
        assert config_ops.get_workstacks_root() == Path("/initial")

        # External modification (simulating another process)
        config_path.write_text(
            """workstacks_root = "/external"
use_graphite = false
""",
            encoding="utf-8",
        )

        # Cache still returns old value (intended behavior)
        assert config_ops.get_workstacks_root() == Path("/initial")

        # After cache invalidation, should read new value
        config_ops._invalidate_cache()
        assert config_ops.get_workstacks_root() == Path("/external")


class TestGlobalConfigDataValidation:
    """Test data validation and error scenarios."""

    def test_config_missing_required_field(self, tmp_path: Path) -> None:
        """Test config with missing workstacks_root field."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """# Missing workstacks_root
use_graphite = true
shell_setup_complete = false
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        with pytest.raises(ValueError, match="Missing 'workstacks_root'"):
            config_ops.get_workstacks_root()

    def test_config_with_invalid_types(self, tmp_path: Path) -> None:
        """Test config with wrong data types."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """workstacks_root = "/test"
use_graphite = "not_a_boolean"
shell_setup_complete = 123
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Should still work - coerced to bool
        assert config_ops.get_use_graphite() is True  # Truthy string
        assert config_ops.get_shell_setup_complete() is True  # Truthy number

    def test_config_with_empty_file(self, tmp_path: Path) -> None:
        """Test config with empty file."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("", encoding="utf-8")

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        with pytest.raises(ValueError, match="Missing 'workstacks_root'"):
            config_ops.get_workstacks_root()

    def test_config_with_whitespace_only(self, tmp_path: Path) -> None:
        """Test config with only whitespace."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("   \n\t\n   ", encoding="utf-8")

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        with pytest.raises(ValueError, match="Missing 'workstacks_root'"):
            config_ops.get_workstacks_root()

    def test_config_path_expansion(self, tmp_path: Path) -> None:
        """Test that paths with ~ are properly expanded."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """workstacks_root = "~/my_workstacks"
use_graphite = false
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        root = config_ops.get_workstacks_root()
        # Should be expanded to absolute path
        assert root.is_absolute()
        assert "~" not in str(root)

    def test_set_with_all_unchanged(self) -> None:
        """Test that set() raises error when all fields are unchanged."""
        config_ops = RealGlobalConfigOps()

        with pytest.raises(ValueError, match="At least one field must be provided"):
            config_ops.set()

    def test_set_new_config_missing_root(self, tmp_path: Path) -> None:
        """Test creating new config without workstacks_root."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        assert not config_ops.exists()

        with pytest.raises(ValueError, match="workstacks_root must be provided"):
            config_ops.set(use_graphite=True)

    def test_config_with_extra_fields(self, tmp_path: Path) -> None:
        """Test config with extra/unknown fields."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """workstacks_root = "/test"
use_graphite = true
unknown_field = "ignored"
future_feature = 42
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Should ignore unknown fields
        assert config_ops.get_workstacks_root() == Path("/test")
        assert config_ops.get_use_graphite() is True


class TestGlobalConfigEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_config_with_very_long_path(self, tmp_path: Path) -> None:
        """Test config with extremely long path value."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        # Create a very long path
        long_path = "/" + "a" * 4000

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        config_ops.set(workstacks_root=Path(long_path))

        # Should handle long paths
        result = config_ops.get_workstacks_root()
        assert len(str(result)) > 4000

    def test_config_with_unicode_characters(self, tmp_path: Path) -> None:
        """Test config with unicode characters in paths."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        unicode_path = tmp_path / "测试目录" / "ワークスタック"
        unicode_path.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        config_ops.set(workstacks_root=unicode_path)

        result = config_ops.get_workstacks_root()
        assert "测试目录" in str(result)
        assert "ワークスタック" in str(result)

    def test_config_repeated_writes(self, tmp_path: Path) -> None:
        """Test repeated writes don't corrupt config."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Perform many rapid writes
        for i in range(100):
            config_ops.set(workstacks_root=Path(f"/test_{i}"))

        # Final state should be consistent
        assert config_ops.get_workstacks_root() == Path("/test_99")

        # File should be valid TOML
        import tomllib

        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        assert data["workstacks_root"] == "/test_99"

    def test_config_partial_update_preserves_other_fields(self, tmp_path: Path) -> None:
        """Test that partial updates preserve other fields."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        # Initial config
        config_ops.set(
            workstacks_root=Path("/test"),
            use_graphite=True,
            shell_setup_complete=True,
            show_pr_info=False,
            show_pr_checks=True,
        )

        # Partial update
        config_ops.set(use_graphite=False)

        # Other fields should be preserved
        assert config_ops.get_workstacks_root() == Path("/test")
        assert config_ops.get_use_graphite() is False  # Updated
        assert config_ops.get_shell_setup_complete() is True  # Preserved
        assert config_ops.get_show_pr_info() is False  # Preserved
        assert config_ops.get_show_pr_checks() is True  # Preserved

    def test_config_handles_interrupted_write(self, tmp_path: Path) -> None:
        """Test behavior when write is interrupted."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        # Write initial valid config
        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path
        config_ops.set(workstacks_root=Path("/initial"))

        # Simulate interrupted write (partial content)
        config_path.write_text("""workstacks_root = "/par""", encoding="utf-8")

        # Should fail to read corrupted config
        import tomllib

        config_ops._invalidate_cache()
        with pytest.raises(tomllib.TOMLDecodeError):
            config_ops.get_workstacks_root()

    def test_config_with_relative_paths(self, tmp_path: Path) -> None:
        """Test that relative paths are resolved to absolute."""
        config_path = tmp_path / ".workstack" / "config.toml"
        config_path.parent.mkdir(parents=True)

        # Write config with relative path
        config_path.write_text(
            """workstacks_root = "./relative/path"
use_graphite = false
""",
            encoding="utf-8",
        )

        config_ops = RealGlobalConfigOps()
        config_ops._path = config_path

        result = config_ops.get_workstacks_root()
        # Should be resolved to absolute
        assert result.is_absolute()
        assert "relative/path" in str(result)
