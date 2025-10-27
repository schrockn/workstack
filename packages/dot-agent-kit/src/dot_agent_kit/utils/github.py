"""GitHub URL utilities for dot-agent."""

import re
from urllib.parse import urlparse


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Parse a GitHub URL to extract owner and repo."""
    # Handle various GitHub URL formats
    patterns = [
        r"github\.com[:/]([^/]+)/([^/\.]+)",
        r"git\+https://github\.com/([^/]+)/([^/\.]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            repo = repo.replace(".git", "")
            return owner, repo

    return None


def github_url_to_package_name(url: str) -> str:
    """Convert a GitHub URL to a likely package name."""
    parts = parse_github_url(url)
    if parts:
        _, repo = parts
        return repo

    # Fallback: extract last part of URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if path_parts:
        return path_parts[-1].replace(".git", "")

    return "unknown"


def is_package_from_github(package_name: str, github_url: str) -> bool:
    """Check if a package was installed from a specific GitHub URL."""
    from dot_agent_kit.utils.packaging import get_package_metadata

    metadata = get_package_metadata(package_name)
    if not metadata:
        return False

    # Check if home page matches
    if metadata.get("home_page") and github_url in metadata["home_page"]:
        return True

    # Check if package name matches repo name
    expected_name = github_url_to_package_name(github_url)
    if package_name == expected_name:
        return True

    return False
