"""Test runner for rebase stacks."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestResult:
    """Result of running tests in a stack."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    command: str


class StackTestRunner:
    """Run tests in rebase stacks."""

    def detect_test_command(self, stack_path: Path) -> str | None:
        """Auto-detect test command from project files.

        Checks for:
        - package.json (npm test)
        - Makefile (make test)
        - pytest.ini / pyproject.toml (pytest)
        - cargo.toml (cargo test)
        - go.mod (go test)

        Returns:
            Detected test command or None
        """
        # Check for Node.js
        if (stack_path / "package.json").exists():
            return "npm test"

        # Check for Python
        if (stack_path / "pytest.ini").exists() or (stack_path / "pyproject.toml").exists():
            return "pytest"

        # Check for Makefile
        makefile_path = stack_path / "Makefile"
        if makefile_path.exists():
            makefile = makefile_path.read_text(encoding="utf-8")
            if "test:" in makefile:
                return "make test"

        # Check for Rust
        if (stack_path / "Cargo.toml").exists():
            return "cargo test"

        # Check for Go
        if (stack_path / "go.mod").exists():
            return "go test ./..."

        return None

    def run_tests(
        self,
        stack_path: Path,
        command: str | None = None,
    ) -> TestResult:
        """Execute tests in the rebase stack.

        Args:
            stack_path: Path to rebase stack worktree
            command: Test command to run (auto-detected if None)

        Returns:
            TestResult with execution details
        """
        if command is None:
            command = self.detect_test_command(stack_path)
            if command is None:
                return TestResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="No test command detected",
                    duration_seconds=0.0,
                    command="",
                )

        start_time = time.time()

        result = subprocess.run(
            command,
            shell=True,
            cwd=stack_path,
            capture_output=True,
            text=True,
            check=False,
        )

        duration = time.time() - start_time

        return TestResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=duration,
            command=command,
        )
