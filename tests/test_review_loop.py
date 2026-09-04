"""Testes do loop de self-healing / review (S4.2)."""

from click.testing import CliRunner

from cli import cli
from core.orchestrator import Orchestrator
from core.parser import load_profile
from core.state import StateManager, StepStatus


def _review_index(profile):
    """Índice (0-based) da etapa de review — a que declara on_reject_return_to."""
    return next(i for i, s in enumerate(profile.steps) if s.on_reject_return_to)


def test_reject_target_by_name_and_default():
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")
    review_idx = _review_index(prof)
    impl_idx = next(i for i, s in enumerate(prof.steps) if s.name == "Implementação")
    # a etapa anterior ao review (Testes) não é a Implementação: a asserção abaixo
    # só prova algo porque as duas resoluções (por nome vs. default) divergem.
    assert impl_idx != review_idx - 1
    assert prof.reject_target_index(review_idx) == impl_idx
    # sem o campo -> etapa anterior
    prof.steps[review_idx].on_reject_return_to = None
    assert prof.reject_target_index(review_idx) == review_idx - 1


def _state_at_review(tmp_path, monkeypatch):
    """Roda backend_clean_arch até travar no gate de review, aprovando qualquer
    gate anterior (ex.: Arquitetura) que apareça no caminho."""
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir="profiles", state_manager=sm)
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")
    review_idx = _review_index(prof)

    state = orch.run_pipeline("backend_clean_arch", auto_approve=False)
    while state.status == "WAITING_APPROVAL" and state.step_states[review_idx].status != StepStatus.WAITING_APPROVAL:
        gate = next(s for s in state.step_states if s.status == StepStatus.WAITING_APPROVAL)
        sm.approve_step("backend_clean_arch", gate.step_index, "arquiteto")
        state = orch.run_pipeline("backend_clean_arch", auto_approve=False, resume=True)

    assert state.step_states[review_idx].status == StepStatus.WAITING_APPROVAL
    return sm, orch, review_idx


def test_reject_twice_then_approve(tmp_path, monkeypatch):
    sm, orch, review_idx = _state_at_review(tmp_path, monkeypatch)
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")
    return_to = prof.reject_target_index(review_idx)

    for cycle in (1, 2):
        st = sm.load_state("backend_clean_arch")
        assert st.step_states[review_idx].status == StepStatus.WAITING_APPROVAL
        sm.register_verdict("backend_clean_arch", review_idx, approved=False, return_to_index=return_to,
                            max_cycles=prof.max_review_cycles, reason=f"acoplamento {cycle}")
        st = sm.load_state("backend_clean_arch")
        assert st.step_states[return_to].status == StepStatus.PENDING  # implementação devolvida
        assert st.step_states[review_idx].review_cycles == cycle
        orch.run_pipeline("backend_clean_arch", auto_approve=False, resume=True)

    # 3ª: aprova
    sm.register_verdict("backend_clean_arch", review_idx, approved=True, return_to_index=return_to,
                        max_cycles=prof.max_review_cycles)
    final = orch.run_pipeline("backend_clean_arch", auto_approve=False, resume=True)
    assert final.status == "COMPLETED"
    assert final.step_states[review_idx].review_cycles == 2
    assert final.step_states[review_idx].approved_by == "revisor"


def test_reject_over_ceiling_fails(tmp_path, monkeypatch):
    sm, _, review_idx = _state_at_review(tmp_path, monkeypatch)
    prof = load_profile("backend_clean_arch", profiles_dir="profiles")
    return_to = prof.reject_target_index(review_idx)
    for _ in range(4):  # teto default 3
        sm.register_verdict("backend_clean_arch", review_idx, approved=False, return_to_index=return_to, max_cycles=3)
    st = sm.load_state("backend_clean_arch")
    assert st.step_states[review_idx].status == StepStatus.FAILED
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
