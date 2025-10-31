"""Tests for suggest-dignified-python.py hook script."""

import json
import subprocess
from pathlib import Path

HOOK_SCRIPT = (
    Path(__file__).parent.parent.parent / ".claude" / "hooks" / "suggest-dignified-python.py"
)
EXPECTED_MESSAGE = "Load the dignified-python skill to abide by Python standards"


def run_hook(tool_name: str, file_path: str) -> tuple[str, int]:
    """Run the hook script with given inputs and return (stdout, exit_code)."""
    input_data = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}

    result = subprocess.run(
        ["python3", str(HOOK_SCRIPT)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )

    return result.stdout.strip(), result.returncode


class TestSuggestDignifiedPythonHook:
    """Test suite for suggest-dignified-python hook."""

    def test_edit_python_file_triggers_suggestion(self):
        """Edit operation on Python file should output suggestion message."""
        stdout, exit_code = run_hook("Edit", "/path/to/src/workstack/config.py")

        assert stdout == EXPECTED_MESSAGE
        assert exit_code == 0

    def test_write_python_file_triggers_suggestion(self):
        """Write operation on Python file should output suggestion message."""
        stdout, exit_code = run_hook("Write", "/path/to/src/workstack/new_module.py")

        assert stdout == EXPECTED_MESSAGE
        assert exit_code == 0

    def test_read_python_file_skips(self):
        """Read operation should not trigger suggestion."""
        stdout, exit_code = run_hook("Read", "/path/to/src/workstack/config.py")

        assert stdout == ""
        assert exit_code == 0

    def test_bash_tool_skips(self):
        """Bash tool should not trigger suggestion."""
        stdout, exit_code = run_hook("Bash", "/path/to/src/workstack/config.py")

        assert stdout == ""
        assert exit_code == 0

    def test_non_python_file_skips(self):
        """Non-Python files should not trigger suggestion."""
        test_cases = [
            "/path/to/README.md",
            "/path/to/config.toml",
            "/path/to/script.sh",
            "/path/to/data.json",
        ]

        for file_path in test_cases:
            stdout, exit_code = run_hook("Edit", file_path)
            assert stdout == "", f"Expected no output for {file_path}"
            assert exit_code == 0

    def test_test_file_with_test_prefix_skips(self):
        """Test files with test_ prefix should skip."""
        stdout, exit_code = run_hook("Edit", "/path/to/tests/test_config.py")

        assert stdout == ""
        assert exit_code == 0

    def test_test_file_with_test_suffix_skips(self):
        """Test files with _test.py suffix should skip."""
        stdout, exit_code = run_hook("Edit", "/path/to/src/config_test.py")

        assert stdout == ""
        assert exit_code == 0

    def test_conftest_file_skips(self):
        """conftest.py files should skip."""
        stdout, exit_code = run_hook("Edit", "/path/to/tests/conftest.py")

        assert stdout == ""
        assert exit_code == 0

    def test_file_in_tests_directory_skips(self):
        """Files in /tests/ directory should skip."""
        stdout, exit_code = run_hook("Edit", "/path/to/tests/helper.py")

        assert stdout == ""
        assert exit_code == 0

    def test_file_in_migrations_directory_skips(self):
        """Files in /migrations/ directory should skip."""
        stdout, exit_code = run_hook("Edit", "/path/to/migrations/version_001.py")

        assert stdout == ""
        assert exit_code == 0

    def test_case_insensitive_pattern_matching(self):
        """Pattern matching should be case insensitive."""
        test_cases = [
            "/path/to/Tests/test_config.py",  # Uppercase Tests
            "/path/to/TEST_CONFIG.PY",  # Uppercase TEST_
            "/path/to/MIGRATIONS/script.py",  # Uppercase MIGRATIONS
        ]

        for file_path in test_cases:
            stdout, exit_code = run_hook("Edit", file_path)
            assert stdout == "", f"Expected skip for case-insensitive pattern: {file_path}"
            assert exit_code == 0

    def test_production_python_files_trigger(self):
        """Production Python files should trigger suggestion."""
        test_cases = [
            "/path/to/src/workstack/config.py",
            "/path/to/src/workstack/cli/commands/create.py",
            "/path/to/src/workstack/core.py",
            "/path/to/packages/my_package/module.py",
        ]

        for file_path in test_cases:
            stdout, exit_code = run_hook("Edit", file_path)
            assert stdout == EXPECTED_MESSAGE, f"Expected trigger for {file_path}"
            assert exit_code == 0

    def test_malformed_json_fails_gracefully(self):
        """Malformed JSON input should fail gracefully without crashing."""
        result = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input="not valid json",
            capture_output=True,
            text=True,
        )

        # Should exit 0 to not disrupt workflow
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_missing_tool_name_field_fails_gracefully(self):
        """Missing tool_name field should fail gracefully."""
        input_data = {"tool_input": {"file_path": "/path/to/config.py"}}

        result = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_missing_tool_input_field_fails_gracefully(self):
        """Missing tool_input field should fail gracefully."""
        input_data = {"tool_name": "Edit"}

        result = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_missing_file_path_field_fails_gracefully(self):
        """Missing file_path field should fail gracefully."""
        input_data = {"tool_name": "Edit", "tool_input": {}}

        result = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_empty_json_object_fails_gracefully(self):
        """Empty JSON object should fail gracefully."""
        result = subprocess.run(
            ["python3", str(HOOK_SCRIPT)],
            input="{}",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_hook_script_exists_and_executable(self):
        """Hook script should exist and be executable."""
        assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"
        assert HOOK_SCRIPT.stat().st_mode & 0o111, "Hook script is not executable"
