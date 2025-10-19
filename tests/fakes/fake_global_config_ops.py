"""Alias for global_config_ops module to support legacy imports.

This module re-exports FakeGlobalConfigOps from global_config_ops.py to maintain
backwards compatibility with test files that use the 'fake_global_config_ops' naming
convention.
"""

from tests.fakes.global_config_ops import FakeGlobalConfigOps

__all__ = ["FakeGlobalConfigOps"]
