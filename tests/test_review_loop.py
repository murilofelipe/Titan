"""Testes do loop de self-healing / review (S4.2)."""

import pytest
from click.testing import CliRunner

from cli import cli
from core.orchestrator import Orchestrator
from core.parser import load_profile
from core.state import StateManager, StepStatus


def test_reject_target_by_name_and_default():
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")
    # review = índice 2, on_reject_return_to = "Implementação Base" = índice 1
    assert prof.reject_target_index(2) == 1
    # sem o campo -> etapa anterior
    prof.steps[2].on_reject_return_to = None
    assert prof.reject_target_index(2) == 1


def _state_at_review(tmp_path, monkeypatch):
    """Roda backend_clean_arch até travar no gate de review (índice 2)."""
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir="profiles", state_manager=sm)
    orch.run_pipeline("backend_clean_arch", auto_approve=False)
    return sm, orch


def test_reject_twice_then_approve(tmp_path, monkeypatch):
    sm, orch = _state_at_review(tmp_path, monkeypatch)
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")

    for cycle in (1, 2):
        st = sm.load_state("backend_clean_arch")
        assert st.step_states[2].status == StepStatus.WAITING_APPROVAL
        sm.register_verdict("backend_clean_arch", 2, approved=False, return_to_index=1,
                            max_cycles=prof.max_review_cycles, reason=f"acoplamento {cycle}")
        st = sm.load_state("backend_clean_arch")
        assert st.step_states[1].status == StepStatus.PENDING  # implementação devolvida
        assert st.step_states[2].review_cycles == cycle
        orch.run_pipeline("backend_clean_arch", auto_approve=False, resume=True)

    # 3ª: aprova
    sm.register_verdict("backend_clean_arch", 2, approved=True, return_to_index=1,
                        max_cycles=prof.max_review_cycles)
    final = orch.run_pipeline("backend_clean_arch", auto_approve=False, resume=True)
    assert final.status == "COMPLETED"
    assert final.step_states[2].review_cycles == 2
    assert final.step_states[2].approved_by == "revisor"


def test_reject_over_ceiling_fails(tmp_path, monkeypatch):
    sm, _ = _state_at_review(tmp_path, monkeypatch)
    for _ in range(4):  # teto default 3
        sm.register_verdict("backend_clean_arch", 2, approved=False, return_to_index=1, max_cycles=3)
    st = sm.load_state("backend_clean_arch")
    assert st.step_states[2].status == StepStatus.FAILED
    assert st.status == "FAILED"


def test_cli_verdict_rejeita(tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    sm = StateManager(state_dir=str(tmp_path / "st"))
    monkeypatch.setattr("cli.StateManager", lambda *a, **k: sm)
    Orchestrator(profiles_dir="profiles", state_manager=sm).run_pipeline("game", auto_approve=False)
    r = CliRunner().invoke(cli, ["verdict", "game", "4", "rejeita", "--motivo", "loop caro"])
    assert r.exit_code == 0, r.output
    assert "volta para 'Implementação'" in r.output
    assert sm.load_state("game").step_states[2].status == StepStatus.PENDING
