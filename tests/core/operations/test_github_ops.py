"""Tests for GitHub operations."""

from workstack.core.github_ops import _parse_github_pr_url


def test_parse_github_pr_url_valid_urls() -> None:
    """Test parsing of valid GitHub PR URLs."""
    # Standard format
    result = _parse_github_pr_url("https://github.com/dagster-io/workstack/pull/23")
    assert result == ("dagster-io", "workstack")

    # Different owner/repo names
    result = _parse_github_pr_url("https://github.com/facebook/react/pull/12345")
    assert result == ("facebook", "react")

    # Single character names
    result = _parse_github_pr_url("https://github.com/a/b/pull/1")
    assert result == ("a", "b")

    # Names with hyphens
    result = _parse_github_pr_url("https://github.com/my-org/my-repo/pull/456")
    assert result == ("my-org", "my-repo")

    # Names with underscores
    result = _parse_github_pr_url("https://github.com/my_org/my_repo/pull/789")
    assert result == ("my_org", "my_repo")

    # Repo names with dots (valid in GitHub)
    result = _parse_github_pr_url("https://github.com/owner/repo.name/pull/100")
    assert result == ("owner", "repo.name")


def test_parse_github_pr_url_invalid_urls() -> None:
    """Test that invalid URLs return None."""
    # Not a GitHub URL
    assert _parse_github_pr_url("https://gitlab.com/owner/repo/pull/123") is None

    # Missing pull number
    assert _parse_github_pr_url("https://github.com/owner/repo/pull/") is None

    # Wrong path structure
    assert _parse_github_pr_url("https://github.com/owner/repo/issues/123") is None

    # Not a URL
    assert _parse_github_pr_url("not a url") is None

    # Empty string
    assert _parse_github_pr_url("") is None

    # Missing repo
    assert _parse_github_pr_url("https://github.com/owner/pull/123") is None


def test_parse_github_pr_url_edge_cases() -> None:
    """Test edge cases in URL parsing.

    Note: The regex is intentionally permissive about trailing content (query params,
    fragments, extra path segments) since it only needs to extract owner/repo from
    GitHub PR URLs returned by gh CLI, which are well-formed.
    """
    # PR number with leading zeros (valid)
    result = _parse_github_pr_url("https://github.com/owner/repo/pull/007")
    assert result == ("owner", "repo")

    # Very long PR number
    result = _parse_github_pr_url("https://github.com/owner/repo/pull/999999999")
    assert result == ("owner", "repo")

    # URL with query parameters (accepted - regex is permissive)
    result = _parse_github_pr_url("https://github.com/owner/repo/pull/123?tab=files")
    assert result == ("owner", "repo")

    # URL with fragment (accepted - regex is permissive)
    result = _parse_github_pr_url("https://github.com/owner/repo/pull/123#discussion")
    assert result == ("owner", "repo")

    # URL with extra path segments (accepted - regex is permissive)
    result = _parse_github_pr_url("https://github.com/owner/repo/pull/123/files")
    assert result == ("owner", "repo")
