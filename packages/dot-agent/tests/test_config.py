from pathlib import Path

from dot_agent import __version__
from dot_agent.config import DotAgentConfig, get_config_path


def test_default_config_uses_package_version() -> None:
    config = DotAgentConfig.default()
    assert config.version == __version__
    assert "tools/gt.md" in config.managed_files


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    config = DotAgentConfig.default()
    config_path = get_config_path(agent_dir)

    config.save(config_path)
    loaded = DotAgentConfig.load(config_path)

    assert loaded == config


def test_load_handles_missing_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".agent" / ".dot-agent.yml"
    loaded = DotAgentConfig.load(config_path)

    assert loaded.managed_files
    assert loaded.exclude == ()
