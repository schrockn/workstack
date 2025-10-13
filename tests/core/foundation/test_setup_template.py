from workstack.cli.commands.init import render_config_template


def test_render_config_template_default() -> None:
    content = render_config_template(preset=None)
    assert "[env]" in content
    assert "[post_create]" in content
    # Contains helpful comments
    assert "EXAMPLE_KEY" in content


def test_render_config_template_dagster() -> None:
    content = render_config_template("dagster")
    assert "DAGSTER_GIT_REPO_DIR" in content
    assert "commands = [" in content
    assert "uv venv" in content
    assert "uv run make dev_install" in content
