from __future__ import annotations

from pathlib import Path


def test_public_example_config_uses_placeholder_datasource_id() -> None:
    example = Path("notion-cli.example.toml").read_text(encoding="utf-8")
    assert 'id = "data-source-id-here"' in example


def test_skill_layer_files_exist() -> None:
    assert Path("skills/notion-cli-agent/SKILL.md").is_file()
    assert Path("skills/notion-cli-agent/agents/openai.yaml").is_file()
    assert Path("skills/notion-cli-agent/references/agent-cli.md").is_file()
    assert Path("skills/notion-cli-agent/references/configuration.md").is_file()


def test_docs_point_to_skill_layer() -> None:
    docs_skill = Path("docs/skill.md").read_text(encoding="utf-8")
    docs_agent = Path("docs/agent-cli.md").read_text(encoding="utf-8")

    assert "skills/notion-cli-agent/SKILL.md" in docs_skill
    assert "skills/notion-cli-agent/references/agent-cli.md" in docs_agent
