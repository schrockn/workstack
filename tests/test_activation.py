from __future__ import annotations

from pathlib import Path

from workstack.activation import render_activation_script


def test_activation_script_contains_expected_lines(tmp_path: Path) -> None:
    wt = tmp_path / ".workstack" / "foo"
    (wt / ".venv" / "bin").mkdir(parents=True)
    (wt / ".venv" / "bin" / "activate").write_text("# venv activate")

    script = render_activation_script(worktree_path=wt)
    # Check key behaviors are present
    assert f"cd '{wt}'" in script
    assert f". '{wt / '.venv' / 'bin' / 'activate'}'" in script
    assert "set -a" in script and "set +a" in script
    assert "./.env" in script
