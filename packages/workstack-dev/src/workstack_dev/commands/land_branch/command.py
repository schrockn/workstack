"""Land a single PR from Graphite stack without affecting upstack branches."""

import json
import subprocess
from dataclasses import asdict, dataclass
from typing import Literal

import click

ErrorType = Literal[
    "parent_not_main",
    "no_pr_found",
    "pr_not_open",
    "multiple_children",
    "merge_failed",
]


@dataclass
class LandBranchSuccess:
    """Success result from landing a branch."""

    success: bool
    pr_number: int
    branch_name: str
    child_branch: str | None
    message: str


@dataclass
class LandBranchError:
    """Error result from landing a branch."""

    success: bool
    error_type: ErrorType
    message: str
    details: dict[str, str | int | list[str]]


def get_current_branch() -> str:
    """Get the name of the current branch."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_branch_metadata(branch_name: str) -> dict | None:
    """Get metadata for a specific branch from workstack graphite branches."""
    result = subprocess.run(
        ["workstack", "graphite", "branches", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    for branch in data["branches"]:
        if branch["name"] == branch_name:
            return branch

    return None


def get_pr_info() -> tuple[int, str] | None:
    """Get PR number and state for current branch. Returns (number, state) or None."""
    result = subprocess.run(
        ["gh", "pr", "view", "--json", "state,number"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    data = json.loads(result.stdout)
    return (data["number"], data["state"])


def merge_pr() -> bool:
    """Merge the PR using squash merge. Returns True on success."""
    result = subprocess.run(
        ["gh", "pr", "merge", "-s"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def navigate_to_child() -> str | None:
    """Navigate to child branch using workstack up. Returns child branch name or None."""
    result = subprocess.run(
        ["workstack", "up"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    return get_current_branch()


def land_branch() -> LandBranchSuccess | LandBranchError:
    """Execute the land-branch workflow. Returns success or error result."""

    # Step 1: Get current branch and metadata
    branch_name = get_current_branch()
    metadata = get_branch_metadata(branch_name)

    if metadata is None:
        return LandBranchError(
            success=False,
            error_type="parent_not_main",
            message=f"Could not find branch metadata for: {branch_name}",
            details={"current_branch": branch_name},
        )

    # Step 2: Validate parent is main
    parent = metadata.get("parent")
    if parent != "main":
        return LandBranchError(
            success=False,
            error_type="parent_not_main",
            message=(
                f"Branch must be exactly one level up from main\n"
                f"Current branch: {branch_name}\n"
                f"Parent branch: {parent} (expected: main)\n\n"
                f"Please navigate to a branch that branches directly from main."
            ),
            details={
                "current_branch": branch_name,
                "parent_branch": parent or "",
            },
        )

    # Step 3: Check PR exists and is open
    pr_info = get_pr_info()
    if pr_info is None:
        return LandBranchError(
            success=False,
            error_type="no_pr_found",
            message=(
                "No pull request found for this branch\n\nPlease create a PR first using: gt submit"
            ),
            details={"current_branch": branch_name},
        )

    pr_number, pr_state = pr_info
    if pr_state != "OPEN":
        return LandBranchError(
            success=False,
            error_type="pr_not_open",
            message=(
                f"Pull request is not open (state: {pr_state})\n\n"
                f"This command only works with open pull requests."
            ),
            details={
                "current_branch": branch_name,
                "pr_number": pr_number,
                "pr_state": pr_state,
            },
        )

    # Step 4: Validate linear stack (0-1 children)
    children = metadata.get("children", [])
    if len(children) > 1:
        return LandBranchError(
            success=False,
            error_type="multiple_children",
            message=(
                f"Branch has multiple children (not a linear stack)\n\n"
                f"Children: {', '.join(children)}\n\n"
                f"This command only works with linear stacks. "
                f"Please use a branch with 0 or 1 children."
            ),
            details={
                "current_branch": branch_name,
                "children": children,
            },
        )

    # Step 5: Merge the PR
    if not merge_pr():
        return LandBranchError(
            success=False,
            error_type="merge_failed",
            message=(f"Failed to merge PR #{pr_number}\n\nPlease resolve the issue and try again."),
            details={
                "current_branch": branch_name,
                "pr_number": pr_number,
            },
        )

    # Step 6: Navigate to child if exists
    child_branch = None
    if len(children) == 1:
        child_branch = navigate_to_child()

    return LandBranchSuccess(
        success=True,
        pr_number=pr_number,
        branch_name=branch_name,
        child_branch=child_branch,
        message=f"Successfully merged PR #{pr_number} for branch {branch_name}",
    )


def format_text_output(result: LandBranchSuccess | LandBranchError) -> str:
    """Format result as user-friendly text."""
    if isinstance(result, LandBranchError):
        return f"Error: {result.message}"

    output = f"✓ {result.message}"

    if result.child_branch:
        output += f"\n✓ Navigated to child branch: {result.child_branch}"
        output += "\n\nYou can now run /land-branch again to merge the next PR in the stack."
    else:
        output += "\n✓ Stack complete! No more branches to land."

    return output


@click.command(name="land-branch")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)",
)
def land_branch_command(format: str) -> None:
    """Merge a single PR from Graphite stack without affecting upstack branches.

    This command safely lands a single branch from a Graphite stack by:

    1. Validating the branch is exactly one level up from main
    2. Checking an open pull request exists
    3. Validating the stack is linear (0 or 1 children)
    4. Squash-merging the PR to main
    5. Navigating to the child branch if one exists
    """
    result = land_branch()

    if format == "json":
        click.echo(json.dumps(asdict(result), indent=2))
    else:
        click.echo(format_text_output(result))

    if isinstance(result, LandBranchError):
        raise SystemExit(1)
