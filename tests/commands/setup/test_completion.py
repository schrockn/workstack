"""Test shell completion generation commands.

This module tests the CLI commands that generate shell completion scripts
for bash, zsh, and fish shells.
"""

import os
import subprocess
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from workstack.cli.commands.completion import completion_bash, completion_fish, completion_zsh


def test_completion_bash_help() -> None:
    """Test bash completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "bash", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    assert "source <(workstack completion bash)" in result.stdout
    assert "bash_completion.d" in result.stdout


def test_completion_zsh_help() -> None:
    """Test zsh completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "zsh", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    assert "source <(workstack completion zsh)" in result.stdout
    assert "compinit" in result.stdout


def test_completion_fish_help() -> None:
    """Test fish completion help shows instructions."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "fish", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    assert "workstack completion fish" in result.stdout
    assert ".config/fish/completions" in result.stdout


def test_completion_bash_generates_script() -> None:
    """Test bash completion generates a script."""
    # Set up environment to generate bash completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "bash_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Bash completion scripts typically contain these
    assert "complete" in result.stdout or "_workstack_completion" in result.stdout


def test_completion_zsh_generates_script() -> None:
    """Test zsh completion generates a script."""
    # Set up environment to generate zsh completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "zsh_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Zsh completion scripts typically start with #compdef
    assert "#compdef" in result.stdout


def test_completion_fish_generates_script() -> None:
    """Test fish completion generates a script."""
    # Set up environment to generate fish completion
    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "fish_source"

    result = subprocess.run(
        ["uv", "run", "workstack"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    # Should generate shell completion code
    assert len(result.stdout) > 100
    # Fish completion scripts typically contain complete command
    assert "complete" in result.stdout


def test_completion_group_help() -> None:
    """Test completion group help lists subcommands."""
    result = subprocess.run(
        ["uv", "run", "workstack", "completion", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0
    assert "bash" in result.stdout
    assert "zsh" in result.stdout
    assert "fish" in result.stdout


# Unit tests that mock subprocess to test the command implementation


@patch("subprocess.run")
@patch("shutil.which")
def test_bash_cmd_generation(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test bash completion command generation."""
    # Setup mocks
    mock_which.return_value = "/usr/local/bin/workstack"
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=(
            "_workstack_completion() {\n"
            "    COMPREPLY=()\n"
            "    local word\n"
            "    complete -F _workstack_completion workstack\n"
            "}"
        ),
    )

    runner = CliRunner()
    result = runner.invoke(completion_bash)

    # Verify command executed successfully
    assert result.exit_code == 0
    assert "_workstack_completion" in result.output
    assert "COMPREPLY" in result.output

    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["/usr/local/bin/workstack"]
    assert call_args[1]["env"]["_WORKSTACK_COMPLETE"] == "bash_source"


@patch("subprocess.run")
@patch("shutil.which")
def test_bash_cmd_includes_all_commands(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test bash completion includes all commands."""
    mock_which.return_value = "/usr/local/bin/workstack"
    # Simulate a more complete bash completion output
    completion_script = """
_workstack_completion() {
    local IFS=$'\t'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" _WORKSTACK_COMPLETE=bash_complete workstack)

    local commands="create list status switch up down rm rename move gc"
    COMPREPLY=($(compgen -W "$commands" -- "${COMP_WORDS[COMP_CWORD]}"))
}

complete -F _workstack_completion workstack
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=completion_script)

    runner = CliRunner()
    result = runner.invoke(completion_bash)

    assert result.exit_code == 0
    # Check for common commands in the output
    assert "create" in result.output
    assert "switch" in result.output
    assert "complete -F _workstack_completion workstack" in result.output


@patch("subprocess.run")
@patch("shutil.which")
def test_bash_cmd_handles_special_chars(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test bash completion handles special characters properly."""
    mock_which.return_value = "/usr/local/bin/workstack"
    # Test with script containing special chars that need escaping
    completion_script = """
_workstack_completion() {
    local word="${COMP_WORDS[COMP_CWORD]}"
    # Handle branch names with special chars
    local branches="feature/test feature-123 bug#456"
    COMPREPLY=($(compgen -W "$branches" -- "$word"))
}
complete -F _workstack_completion workstack
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=completion_script)

    runner = CliRunner()
    result = runner.invoke(completion_bash)

    assert result.exit_code == 0
    assert "COMP_WORDS" in result.output
    assert "compgen" in result.output


@patch("subprocess.run")
@patch("shutil.which")
def test_zsh_cmd_generation(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test zsh completion command generation."""
    mock_which.return_value = "/usr/local/bin/workstack"
    zsh_completion = """#compdef workstack
_workstack() {
    local -a commands
    commands=(
        'create:Create a new workspace'
        'list:List all workspaces'
        'status:Show workspace status'
    )
    _describe 'command' commands
}
compdef _workstack workstack
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=zsh_completion)

    runner = CliRunner()
    result = runner.invoke(completion_zsh)

    assert result.exit_code == 0
    assert "#compdef workstack" in result.output
    assert "_workstack" in result.output
    assert "compdef" in result.output

    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[1]["env"]["_WORKSTACK_COMPLETE"] == "zsh_source"


@patch("subprocess.run")
@patch("shutil.which")
def test_zsh_cmd_includes_descriptions(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test zsh completion includes command descriptions."""
    mock_which.return_value = "/usr/local/bin/workstack"
    zsh_completion = """#compdef workstack
_workstack() {
    local -a commands
    commands=(
        'create:Create a new workspace with an optional branch'
        'list:List all workspaces in the repository'
        'rm:Remove a workspace and its associated branch'
        'switch:Switch to a different workspace'
    )
    _describe 'command' commands
}
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=zsh_completion)

    runner = CliRunner()
    result = runner.invoke(completion_zsh)

    assert result.exit_code == 0
    assert "Create a new workspace" in result.output
    assert "_describe" in result.output


@patch("subprocess.run")
@patch("shutil.which")
def test_zsh_cmd_handles_options(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test zsh completion handles command options."""
    mock_which.return_value = "/usr/local/bin/workstack"
    zsh_completion = """#compdef workstack
_workstack() {
    local context state state_descr line
    typeset -A opt_args

    _arguments \
        '--help[Show help message]' \
        '--version[Show version]' \
        '--verbose[Enable verbose output]' \
        '*::arg:->args'

    case $state in
        args)
            _workstack_commands
            ;;
    esac
}
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=zsh_completion)

    runner = CliRunner()
    result = runner.invoke(completion_zsh)

    assert result.exit_code == 0
    assert "_arguments" in result.output
    assert "--help" in result.output


@patch("subprocess.run")
@patch("shutil.which")
def test_fish_cmd_generation(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test fish completion command generation."""
    mock_which.return_value = "/usr/local/bin/workstack"
    fish_completion = """
complete -c workstack -n "__fish_use_subcommand" -a create -d "Create a new workspace"
complete -c workstack -n "__fish_use_subcommand" -a list -d "List all workspaces"
complete -c workstack -n "__fish_use_subcommand" -a status -d "Show workspace status"
complete -c workstack -l help -d "Show help message"
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=fish_completion)

    runner = CliRunner()
    result = runner.invoke(completion_fish)

    assert result.exit_code == 0
    assert "complete -c workstack" in result.output
    assert "__fish_use_subcommand" in result.output

    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[1]["env"]["_WORKSTACK_COMPLETE"] == "fish_source"


@patch("subprocess.run")
@patch("shutil.which")
def test_fish_cmd_includes_subcommands(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test fish completion includes subcommands."""
    mock_which.return_value = "/usr/local/bin/workstack"
    fish_completion = """
# Main commands
complete -c workstack -n "__fish_use_subcommand" -a create -d "Create a new workspace"
complete -c workstack -n "__fish_use_subcommand" -a switch -d "Switch to a workspace"

# Subcommands for 'create'
complete -c workstack -n "__fish_seen_subcommand_from create" -s f -l force -d "Force creation"
complete -c workstack -n "__fish_seen_subcommand_from create" -s b -l branch -d "Specify branch"
"""
    mock_run.return_value = MagicMock(returncode=0, stdout=fish_completion)

    runner = CliRunner()
    result = runner.invoke(completion_fish)

    assert result.exit_code == 0
    assert "__fish_seen_subcommand_from" in result.output
    assert "-l force" in result.output


@patch("subprocess.run")
@patch("shutil.which")
def test_completion_with_invalid_shell(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test completion with unsupported shell type."""
    # This tests error handling if subprocess fails
    mock_which.return_value = "/usr/local/bin/workstack"
    mock_run.return_value = MagicMock(
        returncode=1, stdout="", stderr="Error: Invalid completion type"
    )

    runner = CliRunner()
    result = runner.invoke(completion_bash)

    # Command should still complete even if subprocess fails
    assert result.exit_code == 0
    # Output should be empty or contain error from subprocess
    assert result.output == ""


@patch("subprocess.run")
@patch("shutil.which")
def test_completion_subprocess_error_handling(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test completion handles subprocess errors gracefully."""
    mock_which.return_value = "/usr/local/bin/workstack"
    # Simulate subprocess raising an exception
    mock_run.side_effect = subprocess.CalledProcessError(1, ["workstack"], stderr="Command failed")

    runner = CliRunner()
    result = runner.invoke(completion_bash)

    # Should not crash, but won't have output
    assert result.exit_code != 0


@patch("subprocess.run")
@patch("shutil.which")
def test_bash_cmd_fallback_when_which_fails(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test bash completion falls back to sys.argv[0] when which() fails."""
    mock_which.return_value = None  # Simulate 'which' not finding workstack
    mock_run.return_value = MagicMock(returncode=0, stdout="completion script")

    runner = CliRunner()
    with patch("sys.argv", ["workstack"]):
        result = runner.invoke(completion_bash)

    assert result.exit_code == 0
    # Verify subprocess was called with fallback
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["workstack"]  # Uses sys.argv[0]


@patch("subprocess.run")
@patch("shutil.which")
def test_zsh_cmd_fallback_when_which_fails(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test zsh completion falls back to sys.argv[0] when which() fails."""
    mock_which.return_value = None
    mock_run.return_value = MagicMock(returncode=0, stdout="#compdef workstack")

    runner = CliRunner()
    with patch("sys.argv", ["workstack"]):
        result = runner.invoke(completion_zsh)

    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["workstack"]


@patch("subprocess.run")
@patch("shutil.which")
def test_fish_cmd_fallback_when_which_fails(mock_which: MagicMock, mock_run: MagicMock) -> None:
    """Test fish completion falls back to sys.argv[0] when which() fails."""
    mock_which.return_value = None
    mock_run.return_value = MagicMock(returncode=0, stdout="complete -c workstack")

    runner = CliRunner()
    with patch("sys.argv", ["workstack"]):
        result = runner.invoke(completion_fish)

    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["workstack"]
