"""Testes dos gates do Épico 4: aprovação (S4.1) e validadores de etapa (S4.3)."""

import pytest
from click.testing import CliRunner

from cli import cli
from core.orchestrator import Orchestrator
from core.parser import StepValidation
from core.state import StateManager, StepStatus
from core.validators import run_validations


# ---------- S4.3: validadores ----------

def test_run_validations_file_and_glob(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "research.md").write_text("x", encoding="utf-8")
    ok = [
        StepValidation(type="file_exists", path="docs/research.md"),
        StepValidation(type="glob_nonempty", pattern="docs/*.md"),
    ]
    assert run_validations(ok, base_dir=str(tmp_path)) == []

    bad = [
        StepValidation(type="file_exists", path="docs/missing.md"),
        StepValidation(type="glob_nonempty", pattern="src/**/*.py"),
    ]
    assert len(run_validations(bad, base_dir=str(tmp_path))) == 2


def test_run_validations_command_zero(tmp_path):
    assert run_validations([StepValidation(type="command_zero", cmd=["true"])], base_dir=str(tmp_path)) == []
    assert run_validations([StepValidation(type="command_zero", cmd=["false"])], base_dir=str(tmp_path)) != []


def _profile(tmp_path, body):
    d = tmp_path / "profiles"
    d.mkdir(exist_ok=True)
    (d / "p.yml").write_text(body, encoding="utf-8")
    return str(d)


def test_orchestrator_fails_step_on_validation(tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    pdir = _profile(tmp_path, (
        "id: p\nname: P\ndescription: d\nsteps:\n"
        "  - name: s1\n    description: d\n    agent: Claude Code\n    expected_output: docs/x.md\n"
        "    validation:\n      - type: file_exists\n        path: docs/x.md\n"
    ))
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir=pdir, state_manager=sm, base_dir=str(tmp_path))
    state = orch.run_pipeline("p", auto_approve=True)
    assert state.status == "FAILED"
    assert state.step_states[0].status == StepStatus.FAILED


# ---------- S4.1: aprovação ----------

def test_auto_approve_records_auto_approver(tmp_path, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir="profiles", state_manager=sm)
    state = orch.run_pipeline("data_engineering", auto_approve=True)
    gate = next(s for s in state.step_states if s.approved_by)
    assert gate.approved_by == "auto"
    assert state.status == "COMPLETED"


def test_approve_before_step_runs_then_resume(tmp_path, monkeypatch):
    """Aprovar uma etapa que ainda não rodou e retomar: ela executa e conclui sem re-prompt."""
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    pdir = _profile(tmp_path, (
        "id: p\nname: P\ndescription: d\nsteps:\n"
        "  - name: rev\n    description: d\n    agent: Antigravity\n    expected_output: o\n    approval_required: true\n"
    ))
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir=pdir, state_manager=sm)
    sm.initialize_state("p", ["rev"])
    sm.approve_step("p", 0, "early")
    state = orch.run_pipeline("p", auto_approve=False, resume=True)
    assert state.status == "COMPLETED"
    assert state.step_states[0].approved_by == "early"


def test_approve_step_out_of_range(tmp_path):
    sm = StateManager(state_dir=str(tmp_path / "st"))
    sm.initialize_state("p", ["a", "b"])
    with pytest.raises(IndexError):
        sm.approve_step("p", 9, "x")


def test_cli_approve_and_status_waiting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # cria estado com um gate travado
    from core.state import PipelineState, StepState
    sm = StateManager()
    st = PipelineState(profile_id="p", status="WAITING_APPROVAL", step_states=[
        StepState(step_index=0, step_name="rev", status=StepStatus.WAITING_APPROVAL),
    ])
    sm.save_state(st)

    r1 = CliRunner().invoke(cli, ["status", "p"])
    assert "Aguardando aprovação" in r1.output

    r2 = CliRunner().invoke(cli, ["approve", "p", "1"])
    assert r2.exit_code == 0 and "aprovada" in r2.output
    assert sm.load_state("p").step_states[0].approved_by
