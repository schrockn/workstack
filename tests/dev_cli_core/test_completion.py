"""Tests for completion helper functions."""

from pathlib import Path

import pytest

from devclikit.completion import (
    _append_to_config,
    _detect_shell,
    _generate_wrapper_script,
    _get_completion_env_var,
    _get_shell_config,
    _is_completion_installed,
)


def test_detect_shell_returns_zsh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that zsh is detected from SHELL environment variable."""
    monkeypatch.setenv("SHELL", "/bin/zsh")

    result = _detect_shell()

    assert result == "zsh"


def test_detect_shell_returns_bash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that bash is detected from SHELL environment variable."""
    monkeypatch.setenv("SHELL", "/bin/bash")

    result = _detect_shell()

    assert result == "bash"


def test_detect_shell_returns_fish(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that fish is detected from SHELL environment variable."""
    monkeypatch.setenv("SHELL", "/usr/local/bin/fish")

    result = _detect_shell()

    assert result == "fish"


def test_detect_shell_exits_when_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that SystemExit is raised for unknown shell."""
    monkeypatch.setenv("SHELL", "/bin/sh")

    with pytest.raises(SystemExit) as exc_info:
        _detect_shell()

    assert exc_info.value.code == 1


def test_detect_shell_exits_when_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that SystemExit is raised when SHELL not set."""
    monkeypatch.delenv("SHELL", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        _detect_shell()

    assert exc_info.value.code == 1


def test_get_shell_config_returns_zshrc() -> None:
    """Test that zsh config path is returned."""
    result = _get_shell_config("zsh")

    assert result == Path.home() / ".zshrc"


def test_get_shell_config_returns_bashrc_when_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that bashrc is preferred when it exists."""
    # Mock home to tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    bashrc = tmp_path / ".bashrc"
    bashrc.touch()

    result = _get_shell_config("bash")

    assert result == bashrc


def test_get_shell_config_returns_bash_profile_when_bashrc_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that bash_profile is returned when bashrc doesn't exist."""
    # Mock home to tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    result = _get_shell_config("bash")

    assert result == tmp_path / ".bash_profile"


def test_get_shell_config_returns_fish_config() -> None:
    """Test that fish config path is returned."""
    result = _get_shell_config("fish")

    assert result == Path.home() / ".config" / "fish" / "config.fish"


def test_get_shell_config_raises_for_unknown_shell() -> None:
    """Test that ValueError is raised for unknown shell."""
    with pytest.raises(ValueError, match="Unknown shell: unknown"):
        _get_shell_config("unknown")


def test_get_completion_env_var_converts_cli_name() -> None:
    """Test that CLI name is converted to env var format."""
    result = _get_completion_env_var("workstack-dev")

    assert result == "_WORKSTACK_DEV_COMPLETE"


def test_get_completion_env_var_handles_single_word() -> None:
    """Test that single-word CLI names work."""
    result = _get_completion_env_var("myapp")

    assert result == "_MYAPP_COMPLETE"


def test_get_completion_env_var_handles_multiple_hyphens() -> None:
    """Test that multiple hyphens are converted."""
    result = _get_completion_env_var("my-cli-tool")

    assert result == "_MY_CLI_TOOL_COMPLETE"


def test_generate_wrapper_script_creates_bash_wrapper() -> None:
    """Test that bash wrapper script is generated correctly."""
    result = _generate_wrapper_script("my-cli", "bash")

    assert "my-cli()" in result
    assert "unset -f my-cli" in result
    assert "_MY_CLI_COMPLETE" in result
    assert "source <(my-cli completion bash" in result
    assert "command my-cli" in result


def test_generate_wrapper_script_creates_zsh_wrapper() -> None:
    """Test that zsh wrapper script is generated correctly."""
    result = _generate_wrapper_script("my-cli", "zsh")

    assert "my-cli()" in result
    assert "unfunction my-cli" in result
    assert "_MY_CLI_COMPLETE" in result
    assert "source <(my-cli completion zsh" in result
    assert "command my-cli" in result


def test_generate_wrapper_script_creates_fish_wrapper() -> None:
    """Test that fish wrapper script is generated correctly."""
    result = _generate_wrapper_script("my-cli", "fish")

    assert "function my-cli" in result
    assert "functions -e my-cli" in result
    assert "_MY_CLI_COMPLETE" in result
    assert "my-cli completion fish" in result
    assert "command my-cli" in result


def test_generate_wrapper_script_raises_for_unknown_shell() -> None:
    """Test that ValueError is raised for unknown shell."""
    with pytest.raises(ValueError, match="Unknown shell: unknown"):
        _generate_wrapper_script("my-cli", "unknown")


def test_is_completion_installed_returns_false_when_file_missing(tmp_path: Path) -> None:
    """Test that False is returned when config file doesn't exist."""
    config_file = tmp_path / ".zshrc"

    result = _is_completion_installed(config_file, "my-cli")

    assert result is False


def test_is_completion_installed_returns_false_when_marker_missing(tmp_path: Path) -> None:
    """Test that False is returned when marker not in file."""
    config_file = tmp_path / ".zshrc"
    config_file.write_text("some other content\n", encoding="utf-8")

    result = _is_completion_installed(config_file, "my-cli")

    assert result is False


def test_is_completion_installed_returns_true_when_marker_present(tmp_path: Path) -> None:
    """Test that True is returned when marker is found."""
    config_file = tmp_path / ".zshrc"
    config_file.write_text(
        "# my-cli completion - added by devclikit\nsome content\n",
        encoding="utf-8",
    )

    result = _is_completion_installed(config_file, "my-cli")

    assert result is True


def test_append_to_config_creates_file_with_snippet(tmp_path: Path) -> None:
    """Test that config file is created with snippet."""
    config_file = tmp_path / ".zshrc"
    snippet = "source <(my-cli completion zsh)"

    _append_to_config(config_file, snippet, "my-cli")

    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert "# my-cli completion - added by devclikit" in content
    assert snippet in content


def test_append_to_config_appends_to_existing_file(tmp_path: Path) -> None:
    """Test that snippet is appended to existing file."""
    config_file = tmp_path / ".zshrc"
    config_file.write_text("existing content\n", encoding="utf-8")
    snippet = "source <(my-cli completion zsh)"

    _append_to_config(config_file, snippet, "my-cli")

    content = config_file.read_text(encoding="utf-8")
    assert "existing content" in content
    assert "# my-cli completion - added by devclikit" in content
    assert snippet in content


def test_append_to_config_creates_parent_directories(tmp_path: Path) -> None:
    """Test that parent directories are created."""
    config_file = tmp_path / "nested" / "dir" / ".config" / "fish" / "config.fish"
    snippet = "my-cli completion fish | source"

    _append_to_config(config_file, snippet, "my-cli")

    assert config_file.exists()
    assert config_file.parent.exists()


def test_append_to_config_exits_when_already_installed(tmp_path: Path) -> None:
    """Test that SystemExit is raised when already installed."""
    config_file = tmp_path / ".zshrc"
    config_file.write_text(
        "# my-cli completion - added by devclikit\nsome content\n",
        encoding="utf-8",
    )
    snippet = "new snippet"

    with pytest.raises(SystemExit) as exc_info:
        _append_to_config(config_file, snippet, "my-cli")

    assert exc_info.value.code == 1


def test_append_to_config_preserves_existing_content(tmp_path: Path) -> None:
    """Test that existing content is not modified."""
    config_file = tmp_path / ".zshrc"
    original_content = "# Original comment\nexport PATH=/usr/local/bin:$PATH\n"
    config_file.write_text(original_content, encoding="utf-8")
    snippet = "source <(my-cli completion zsh)"

    _append_to_config(config_file, snippet, "my-cli")

    content = config_file.read_text(encoding="utf-8")
    assert original_content in content
    assert snippet in content
