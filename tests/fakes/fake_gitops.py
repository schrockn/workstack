"""Alias for gitops module to support legacy imports.

This module re-exports FakeGitOps from gitops.py to maintain backwards
compatibility with test files that use the 'fake_gitops' naming convention.
"""

from tests.fakes.gitops import FakeGitOps

__all__ = ["FakeGitOps"]
