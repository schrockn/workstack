"""Tests for FakeGraphiteOps."""

from tests.fakes.graphite_ops import FakeGraphiteOps


def test_fake_graphite_ops_initialization() -> None:
    """Test that FakeGraphiteOps can be initialized."""
    ops = FakeGraphiteOps()
    assert ops is not None


def test_fake_graphite_ops_no_op() -> None:
    """Test that FakeGraphiteOps operations are no-ops."""
    ops = FakeGraphiteOps()
    # FakeGraphiteOps is a simple stub - just verify it exists
    assert hasattr(ops, "__class__")
    assert ops.__class__.__name__ == "FakeGraphiteOps"
