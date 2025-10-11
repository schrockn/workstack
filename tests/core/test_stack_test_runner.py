"""Tests for stack test runner."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from workstack.core.stack_test_runner import StackTestRunner, TestResult


class TestDetectTestCommand:
    """Tests for test command detection."""

    def test_detect_npm_test(self, tmp_path: Path) -> None:
        """Detects npm test when package.json exists."""
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "npm test"

    def test_detect_pytest_from_pytest_ini(self, tmp_path: Path) -> None:
        """Detects pytest when pytest.ini exists."""
        (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "pytest"

    def test_detect_pytest_from_pyproject_toml(self, tmp_path: Path) -> None:
        """Detects pytest when pyproject.toml exists."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "pytest"

    def test_detect_make_test(self, tmp_path: Path) -> None:
        """Detects make test when Makefile has test target."""
        (tmp_path / "Makefile").write_text("test:\n\tpytest", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "make test"

    def test_detect_make_test_not_detected_without_target(self, tmp_path: Path) -> None:
        """Does not detect make test when Makefile lacks test target."""
        (tmp_path / "Makefile").write_text("build:\n\tgcc main.c", encoding="utf-8")
        runner = StackTestRunner()
        # Should continue checking other options
        assert runner.detect_test_command(tmp_path) is None

    def test_detect_cargo_test(self, tmp_path: Path) -> None:
        """Detects cargo test when Cargo.toml exists."""
        (tmp_path / "Cargo.toml").write_text("[package]", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "cargo test"

    def test_detect_go_test(self, tmp_path: Path) -> None:
        """Detects go test when go.mod exists."""
        (tmp_path / "go.mod").write_text("module example", encoding="utf-8")
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) == "go test ./..."

    def test_detect_no_test_command(self, tmp_path: Path) -> None:
        """Returns None when no test command can be detected."""
        runner = StackTestRunner()
        assert runner.detect_test_command(tmp_path) is None

    def test_detect_prioritizes_package_json(self, tmp_path: Path) -> None:
        """Prioritizes package.json over other markers."""
        # Create multiple project markers
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
        (tmp_path / "Cargo.toml").write_text("[package]", encoding="utf-8")

        runner = StackTestRunner()
        # Should return npm test first
        assert runner.detect_test_command(tmp_path) == "npm test"


class TestRunTests:
    """Tests for test execution."""

    @patch("workstack.core.stack_test_runner.subprocess.run")
    def test_run_tests_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Runs tests successfully and returns success result."""
        # Mock successful test run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="All tests passed\n",
            stderr="",
        )

        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command="pytest")

        # Verify subprocess was called correctly
        mock_run.assert_called_once_with(
            "pytest",
            shell=True,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

        # Verify result
        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "All tests passed\n"
        assert result.stderr == ""
        assert result.command == "pytest"
        assert result.duration_seconds >= 0

    @patch("workstack.core.stack_test_runner.subprocess.run")
    def test_run_tests_failure(self, mock_run: Mock, tmp_path: Path) -> None:
        """Runs tests that fail and returns failure result."""
        # Mock failed test run
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="FAILED test_foo.py::test_bar\n",
        )

        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command="pytest")

        # Verify result
        assert result.success is False
        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == "FAILED test_foo.py::test_bar\n"
        assert result.command == "pytest"

    @patch("workstack.core.stack_test_runner.subprocess.run")
    def test_run_tests_with_auto_detection(self, mock_run: Mock, tmp_path: Path) -> None:
        """Auto-detects and runs test command when not specified."""
        # Set up auto-detection
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")

        # Mock successful test run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Tests passed\n",
            stderr="",
        )

        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command=None)

        # Verify npm test was auto-detected and used
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "npm test"
        assert result.command == "npm test"
        assert result.success is True

    def test_run_tests_no_command_detected(self, tmp_path: Path) -> None:
        """Returns error result when no command detected and none provided."""
        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command=None)

        # Verify error result
        assert result.success is False
        assert result.exit_code == -1
        assert result.stdout == ""
        assert result.stderr == "No test command detected"
        assert result.duration_seconds == 0.0
        assert result.command == ""

    @patch("workstack.core.stack_test_runner.subprocess.run")
    @patch("workstack.core.stack_test_runner.time.time")
    def test_run_tests_measures_duration(
        self, mock_time: Mock, mock_run: Mock, tmp_path: Path
    ) -> None:
        """Accurately measures test execution duration."""
        # Mock time to simulate 2.5 second execution
        mock_time.side_effect = [100.0, 102.5]

        # Mock test run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command="pytest")

        # Verify duration
        assert result.duration_seconds == 2.5

    @patch("workstack.core.stack_test_runner.subprocess.run")
    def test_run_tests_captures_output(self, mock_run: Mock, tmp_path: Path) -> None:
        """Captures both stdout and stderr from test execution."""
        # Mock test with output on both streams
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Test output line 1\nTest output line 2\n",
            stderr="Warning: deprecated API\n",
        )

        runner = StackTestRunner()
        result = runner.run_tests(tmp_path, command="pytest")

        # Verify both outputs captured
        assert "Test output line 1" in result.stdout
        assert "Test output line 2" in result.stdout
        assert "Warning: deprecated API" in result.stderr


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_immutable(self) -> None:
        """TestResult is immutable (frozen)."""
        result = TestResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=1.5,
            command="pytest",
        )

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]

    def test_test_result_attributes(self) -> None:
        """TestResult stores all attributes correctly."""
        result = TestResult(
            success=True,
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            duration_seconds=2.5,
            command="npm test",
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "All tests passed"
        assert result.stderr == ""
        assert result.duration_seconds == 2.5
        assert result.command == "npm test"
