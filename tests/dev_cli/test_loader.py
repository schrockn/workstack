"""Tests for command loader."""

import click

from workstack.dev_cli.loader import load_commands


def test_load_commands_finds_valid_commands() -> None:
    """Test that loader discovers valid commands."""
    commands = load_commands()
    assert "clean-cache" in commands
    assert isinstance(commands["clean-cache"], click.Command)
    assert "publish-to-pypi" in commands
    assert isinstance(commands["publish-to-pypi"], click.Command)


def test_load_commands_converts_snake_to_kebab() -> None:
    """Test that snake_case dirs become kebab-case commands."""
    commands = load_commands()
    # clean_cache directory should become clean-cache command
    assert "clean-cache" in commands
    # publish_to_pypi directory should become publish-to-pypi command
    assert "publish-to-pypi" in commands
