"""Unit tests for core/parser.py pipeline profile parsing and schema validation."""

import os
import pytest
from pydantic import ValidationError
from core.parser import parse_pipeline, load_profile, PipelineProfile, AgentStep


def test_parse_existing_profiles():
    """Verify successful parsing of existing profiles (data_engineering.yml, backend_clean_arch.yml)."""
    # Test data_engineering profile via parse_pipeline and load_profile
    profile_de = load_profile("data_engineering", profiles_dir="profiles")
    assert isinstance(profile_de, PipelineProfile)
    assert profile_de.id == "data_engineering"
    assert profile_de.name == "Engenharia de Dados (Freelance)"
    assert len(profile_de.steps) == 3
    assert profile_de.steps[0].name == "Levantamento e Entendimento dos Dados"
    assert profile_de.steps[0].agent == "Claude Code"
    assert profile_de.steps[0].context_files == ["shared_context/rules/python_clean_code.md"]
    assert profile_de.steps[0].approval_required is False

    # Test backend_clean_arch profile via parse_pipeline directly
    backend_path = os.path.join("profiles", "backend_clean_arch.yml")
    profile_backend = parse_pipeline(backend_path)
    assert isinstance(profile_backend, PipelineProfile)
    assert profile_backend.id == "backend_clean_arch"
    assert len(profile_backend.steps) == 3
    assert profile_backend.steps[2].agent == "Antigravity"


def test_file_not_found():
    """Verify FileNotFoundError is raised when profile file is missing."""
    with pytest.raises(FileNotFoundError):
        parse_pipeline("profiles/non_existent_profile.yml")

    with pytest.raises(FileNotFoundError):
        load_profile("non_existent_id", profiles_dir="profiles")


def test_corrupt_yaml_syntax(tmp_path):
    """Verify ValueError is raised when YAML syntax is corrupt."""
    bad_yaml = tmp_path / "corrupt.yml"
    bad_yaml.write_text("id: 'test'\nname: [unclosed_list: : invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML syntax"):
        parse_pipeline(str(bad_yaml))


def test_non_dict_yaml_content(tmp_path):
    """Verify ValueError is raised when top-level YAML is not a dictionary/mapping."""
    list_yaml = tmp_path / "list.yml"
    list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected a dictionary"):
        parse_pipeline(str(list_yaml))


def test_missing_required_fields(tmp_path):
    """Verify ValidationError is raised when required profile fields are missing."""
    incomplete_yaml = tmp_path / "incomplete.yml"
    incomplete_yaml.write_text("""
id: "test_inc"
description: "Missing name and steps"
""", encoding="utf-8")

    with pytest.raises(ValidationError):
        parse_pipeline(str(incomplete_yaml))


def test_missing_step_required_fields(tmp_path):
    """Verify ValidationError is raised when a step is missing required fields (agent, expected_output)."""
    invalid_step_yaml = tmp_path / "invalid_step.yml"
    invalid_step_yaml.write_text("""
id: "test_step"
name: "Test Step Profile"
description: "Profile with invalid step"
steps:
  - name: "Step 1"
    description: "Incomplete step missing agent and expected_output"
""", encoding="utf-8")

    with pytest.raises(ValidationError):
        parse_pipeline(str(invalid_step_yaml))


def test_optional_fields_parsing(tmp_path):
    """Verify default values and explicit values for optional fields (approval_required, context_files)."""
    # Profile with explicit optional fields
    explicit_yaml = tmp_path / "explicit.yml"
    explicit_yaml.write_text("""
id: "explicit_profile"
name: "Explicit Profile"
description: "Testing explicit optional fields"
steps:
  - name: "Step 1"
    description: "Step with explicit context and approval"
    agent: "TestAgent"
    context_files: ["file1.txt", "file2.py"]
    expected_output: "Done"
    approval_required: true
""", encoding="utf-8")

    profile_exp = parse_pipeline(str(explicit_yaml))
    assert profile_exp.steps[0].context_files == ["file1.txt", "file2.py"]
    assert profile_exp.steps[0].approval_required is True

    # Profile omitting optional fields to verify default values
    defaults_yaml = tmp_path / "defaults.yml"
    defaults_yaml.write_text("""
id: "default_profile"
name: "Default Profile"
description: "Testing default optional fields"
steps:
  - name: "Step 1"
    description: "Minimal step"
    agent: "TestAgent"
    expected_output: "Done"
""", encoding="utf-8")

    profile_def = parse_pipeline(str(defaults_yaml))
    assert profile_def.steps[0].context_files == []
    assert profile_def.steps[0].approval_required is False


def test_load_profile_yaml_extension(tmp_path):
    """Verify load_profile handles both .yml and .yaml files."""
    yaml_profile = tmp_path / "custom_profile.yaml"
    yaml_profile.write_text("""
id: "custom_profile"
name: "Custom Profile YAML"
description: "Testing .yaml extension support"
steps:
  - name: "Step 1"
    description: "Sample step"
    agent: "TestAgent"
    expected_output: "Output"
""", encoding="utf-8")

    loaded = load_profile("custom_profile", profiles_dir=str(tmp_path))
    assert loaded.id == "custom_profile"
    assert loaded.name == "Custom Profile YAML"
