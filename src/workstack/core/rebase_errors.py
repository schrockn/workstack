"""Enhanced error handling for rebase operations."""

import click


class RebaseError(Exception):
    """Base exception for rebase errors with user-friendly suggestions."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """Initialize rebase error with message and optional suggestion.

        Args:
            message: Error message describing what went wrong
            suggestion: Optional suggestion for how to resolve the issue
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class RebaseConflictError(RebaseError):
    """Raised when rebase encounters conflicts."""

    def __init__(self, files: list[str], branch: str) -> None:
        """Initialize conflict error with list of conflicted files.

        Args:
            files: List of files with conflicts
            branch: Branch being rebased
        """
        message = f"Rebase has conflicts in {len(files)} file(s)"
        suggestion = f"Run 'workstack rebase resolve {branch}' to resolve conflicts interactively"
        super().__init__(message, suggestion)
        self.files = files
        self.branch = branch


class RebaseStackNotFoundError(RebaseError):
    """Raised when expected rebase stack doesn't exist."""

    def __init__(self, branch: str) -> None:
        """Initialize stack not found error.

        Args:
            branch: Branch that should have a stack
        """
        message = f"No rebase stack found for branch '{branch}'"
        suggestion = f"Run 'workstack rebase preview {branch}' to create a rebase stack first"
        super().__init__(message, suggestion)
        self.branch = branch


class RebaseInProgressError(RebaseError):
    """Raised when attempting operation while rebase is in progress."""

    def __init__(self, branch: str) -> None:
        """Initialize rebase in progress error.

        Args:
            branch: Branch with in-progress rebase
        """
        message = f"Rebase is still in progress for branch '{branch}'"
        suggestion = "Complete the rebase or run 'workstack rebase abort' to cancel"
        super().__init__(message, suggestion)
        self.branch = branch


class RebaseTestFailedError(RebaseError):
    """Raised when tests fail in rebase stack."""

    def __init__(self, branch: str, exit_code: int) -> None:
        """Initialize test failed error.

        Args:
            branch: Branch being tested
            exit_code: Test command exit code
        """
        message = f"Tests failed in rebase stack for '{branch}' (exit code: {exit_code})"
        suggestion = "Fix the tests in the rebase stack or use --force to apply anyway"
        super().__init__(message, suggestion)
        self.branch = branch
        self.exit_code = exit_code


def handle_rebase_error(error: RebaseError) -> None:
    """Display user-friendly error message with suggestions.

    Args:
        error: RebaseError to display
    """
    # Display error message
    click.echo(click.style(f"Error: {error.message}", fg="red", bold=True), err=True)

    # Display suggestion if available
    if error.suggestion:
        click.echo(f"\n{click.style('💡 Suggestion:', fg='yellow')} {error.suggestion}", err=True)

    # Show common troubleshooting commands
    click.echo(f"\n{click.style('Troubleshooting:', fg='cyan')}", err=True)
    click.echo("  • workstack rebase status   (check current state)", err=True)
    click.echo("  • workstack rebase abort    (cancel and clean up)", err=True)
    click.echo("  • workstack list            (see all worktrees)", err=True)
