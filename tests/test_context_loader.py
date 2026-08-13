import os
import pytest
from core.context_loader import (
    ContextItem,
    LoadedStepContext,
    load_context_file,
    load_step_context,
    format_context_for_prompt,
)


def test_load_context_file_existing(tmp_path):
    test_file = tmp_path / "rules.md"
    content = "# Rules\n- Use clean architecture"
    test_file.write_text(content, encoding="utf-8")

    item = load_context_file(str(test_file))

    assert item.file_path == str(test_file)
    assert item.exists is True
    assert item.content == content
    assert item.error is None


def test_load_context_file_relative_path(tmp_path):
    sub_dir = tmp_path / "shared"
    sub_dir.mkdir()
    rel_file = sub_dir / "skill.md"
    content = "# Skill\n- dbt modeling"
    rel_file.write_text(content, encoding="utf-8")

    item = load_context_file("shared/skill.md", base_dir=str(tmp_path))

    assert item.file_path == "shared/skill.md"
    assert item.exists is True
    assert item.content == content
    assert item.error is None


def test_load_context_file_missing(tmp_path):
    item = load_context_file("non_existent_file.md", base_dir=str(tmp_path))

    assert item.file_path == "non_existent_file.md"
    assert item.exists is False
    assert item.content is None
    assert item.error is not None
    assert "File not found" in item.error


def test_load_context_file_directory(tmp_path):
    sub_dir = tmp_path / "test_dir"
    sub_dir.mkdir()

    item = load_context_file("test_dir", base_dir=str(tmp_path))

    assert item.file_path == "test_dir"
    assert item.exists is False
    assert item.error is not None
    assert "Path is not a file" in item.error


def test_load_step_context_mixed(tmp_path):
    f1 = tmp_path / "f1.md"
    f1.write_text("Content 1", encoding="utf-8")

    files = ["f1.md", "missing.md"]
    loaded = load_step_context(files, base_dir=str(tmp_path), step_name="Step 1")

    assert loaded.step_name == "Step 1"
    assert not loaded.is_empty()
    assert len(loaded.items) == 2
    assert loaded.items["f1.md"].exists is True
    assert loaded.items["f1.md"].content == "Content 1"
    assert loaded.items["missing.md"].exists is False


def test_loaded_step_context_empty():
    loaded = LoadedStepContext()
    assert loaded.is_empty() is True

    context_str = format_context_for_prompt(loaded)
    assert context_str == ""


def test_format_context_for_prompt_valid_and_missing(tmp_path):
    f1 = tmp_path / "rule.md"
    f1.write_text("DO NOT CHEAT", encoding="utf-8")

    loaded = load_step_context(["rule.md", "missing.md"], base_dir=str(tmp_path))
    formatted = format_context_for_prompt(loaded)

    assert "### 📂 Contexto Injetado Automático" in formatted
    assert "#### Arquivo: `rule.md`" in formatted
    assert "```markdown\nDO NOT CHEAT\n```" in formatted
    assert "⚠️ **Aviso (missing.md)**" in formatted
