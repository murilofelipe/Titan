"""Testes do registry de agentes (S3.1)."""

import pytest

from core.classifier import get_available_profiles
from core.orchestrator import Orchestrator
from core.parser import (
    load_agent_registry,
    load_profile,
    validate_profile_agents,
    AgentStep,
    PipelineProfile,
)
from core.state import StateManager

CANONICAL = {"Perplexity", "Claude Code", "Cursor", "Antigravity", "Codex CLI"}


def test_registry_loads_with_five_roles():
    reg = load_agent_registry()
    assert set(reg.names()) == CANONICAL
    for a in reg.agents:
        assert a.role and a.instructions  # bloco de instrução das stories 3.2–3.6


def test_all_shipped_profiles_use_registry_agents():
    reg = load_agent_registry()
    for pid in get_available_profiles("profiles"):
        assert validate_profile_agents(load_profile(pid, profiles_dir="profiles"), reg) == []


def test_validate_flags_unknown_agent():
    prof = PipelineProfile(
        id="x", name="x", description="x",
        steps=[AgentStep(name="s", description="d", agent="Junie", expected_output="o")],
    )
    assert validate_profile_agents(prof) == ["Junie"]


def test_orchestrator_rejects_unknown_agent(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "bad.yml").write_text(
        "id: bad\nname: Bad\ndescription: d\n"
        "steps:\n  - name: s\n    description: d\n    agent: NopeAgent\n    expected_output: o\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    orch = Orchestrator(profiles_dir=str(profiles_dir), state_manager=StateManager(state_dir=str(tmp_path / "st")))
    with pytest.raises(ValueError, match="fora do registry"):
        orch.run_pipeline("bad", auto_approve=True)
