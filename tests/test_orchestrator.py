import pytest

from core.orchestrator import Orchestrator
from core.state import StateManager, StepStatus


def _run_through_gates(orchestrator, sm, profile_id, approver="tester"):
    """Roda (ou retoma) até concluir, aprovando cada gate que travar no caminho."""
    state = orchestrator.run_pipeline(profile_id, auto_approve=False, resume=True)
    while state.status == "WAITING_APPROVAL":
        gate = next(s for s in state.step_states if s.status == StepStatus.WAITING_APPROVAL)
        sm.approve_step(profile_id, gate.step_index, approver)
        state = orchestrator.run_pipeline(profile_id, auto_approve=False, resume=True)
    return state


def test_orchestrator_run_pipeline_auto_mode(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)

    # Input should not be called in auto mode
    def mock_input(prompt=""):
        pytest.fail("input() should not be called when auto_approve=True")

    monkeypatch.setattr("builtins.input", mock_input)

    state = orchestrator.run_pipeline("data_engineering", auto_approve=True)

    assert state is not None
    assert state.profile_id == "data_engineering"
    assert state.status == "COMPLETED"
    assert len(state.step_states) > 0
    assert all(step.status == StepStatus.COMPLETED for step in state.step_states)


def test_orchestrator_run_pipeline_interactive(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)

    input_calls = []

    def mock_input(prompt=""):
        input_calls.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", mock_input)

    # backend_clean_arch tem approval_required em mais de uma etapa (Arquitetura,
    # Review): o run interativo para no primeiro gate (S4.1) em vez de concluir sozinho.
    state = orchestrator.run_pipeline("backend_clean_arch", auto_approve=False)

    assert state is not None
    assert state.profile_id == "backend_clean_arch"
    assert state.status == "WAITING_APPROVAL"
    first_gate = next(s for s in state.step_states if s.status == StepStatus.WAITING_APPROVAL)
    assert all(
        s.status == StepStatus.COMPLETED for s in state.step_states if s.step_index < first_gate.step_index
    )

    # Ciclo completo: aprova cada gate que aparecer no caminho até concluir.
    from core.parser import load_profile
    profile = load_profile("backend_clean_arch", profiles_dir="profiles")
    final = _run_through_gates(orchestrator, sm, "backend_clean_arch")
    assert final.status == "COMPLETED"
    assert all(step.status == StepStatus.COMPLETED for step in final.step_states)
    for step, sstate in zip(profile.steps, final.step_states):
        if step.approval_required:
            assert sstate.approved_by == "tester"


def test_orchestrator_resume_after_approval_does_not_rerun_step(tmp_path, monkeypatch):
    """Guarda o branch WAITING_APPROVAL+approved_by: retomar um gate já aprovado
    conclui a etapa sem chamar input() de novo para ela (`game` tem 1 só gate)."""
    from core.parser import load_profile

    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)
    profile = load_profile("game", profiles_dir="profiles")

    input_calls = []
    monkeypatch.setattr("builtins.input", lambda prompt="": input_calls.append(prompt))

    state = orchestrator.run_pipeline("game", auto_approve=False)
    assert state.status == "WAITING_APPROVAL"
    assert len(input_calls) == len(profile.steps)  # 1 input por etapa, incluindo o gate

    gate = next(s for s in state.step_states if s.status == StepStatus.WAITING_APPROVAL)
    sm.approve_step("game", gate.step_index, "tester")
    final = orchestrator.run_pipeline("game", auto_approve=False, resume=True)

    assert final.status == "COMPLETED"
    assert len(input_calls) == len(profile.steps)  # retomada não chamou input() de novo


def test_orchestrator_run_pipeline_classification(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)

    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    # Prompt matching backend clean architecture
    state = orchestrator.run_pipeline("build FastAPI microservice clean arch API", auto_approve=True)

    assert state is not None
    assert state.profile_id == "backend_clean_arch"
    assert state.status == "COMPLETED"


def test_orchestrator_resume_mode(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)

    # Initialize state manually and mark step 0 as COMPLETED
    from core.parser import load_profile
    profile = load_profile("data_engineering", profiles_dir="profiles")
    sm.initialize_state("data_engineering", profile.steps)
    sm.update_step_status("data_engineering", 0, StepStatus.COMPLETED)

    assert sm.get_resume_step("data_engineering") == 1

    input_calls = []

    def mock_input(prompt=""):
        input_calls.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", mock_input)

    state = orchestrator.run_pipeline("data_engineering", auto_approve=False, resume=True)

    assert state is not None
    # data_engineering tem mais de um gate: o run para no primeiro que encontrar
    # depois do step 0 (já concluído antes do resume).
    assert state.status == "WAITING_APPROVAL"
    assert len(input_calls) >= 1

    final = _run_through_gates(orchestrator, sm, "data_engineering")
    assert final.status == "COMPLETED"
    assert all(step.status == StepStatus.COMPLETED for step in final.step_states)


def test_orchestrator_reset_mode(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(profiles_dir="profiles", state_manager=sm)

    # First run: set step 0 completed
    from core.parser import load_profile
    profile = load_profile("data_engineering", profiles_dir="profiles")
    sm.initialize_state("data_engineering", profile.steps)
    sm.update_step_status("data_engineering", 0, StepStatus.COMPLETED)

    # Reset run
    state = orchestrator.run_pipeline("data_engineering", auto_approve=True, reset=True)

    assert state is not None
    assert state.status == "COMPLETED"
    assert state.current_step_index == len(profile.steps)


def test_orchestrator_context_injection_and_artifacts(tmp_path, monkeypatch, capsys):
    rules_dir = tmp_path / "shared_context" / "rules"
    rules_dir.mkdir(parents=True)
    rule_file = rules_dir / "python_clean_code.md"
    rule_file.write_text("# PEP 8 Rules\nUse snake_case", encoding="utf-8")

    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir(parents=True)
    profile_content = """
id: test_profile
name: Test Profile
description: Profile for testing context injection
steps:
  - name: Step With Context
    description: Execute step 1
    agent: Claude Code
    context_files:
      - shared_context/rules/python_clean_code.md
    expected_output: Done
  - name: Step Without Context
    description: Execute step 2
    agent: Antigravity
    context_files: []
    expected_output: Approved
"""
    (profiles_dir / "test_profile.yml").write_text(profile_content, encoding="utf-8")

    state_dir = str(tmp_path / "titan_state")
    sm = StateManager(state_dir=state_dir)
    orchestrator = Orchestrator(
        profiles_dir=str(profiles_dir),
        state_manager=sm,
        base_dir=str(tmp_path)
    )

    state = orchestrator.run_pipeline("test_profile", auto_approve=True)

    assert state is not None
    assert state.status == "COMPLETED"
    assert len(state.step_states) == 2

    # Step 0 should have loaded_context artifact
    step0 = state.step_states[0]
    assert "loaded_context" in step0.artifacts
    loaded_ctx0 = step0.artifacts["loaded_context"]
    assert "items" in loaded_ctx0
    assert "shared_context/rules/python_clean_code.md" in loaded_ctx0["items"]
    ctx_item = loaded_ctx0["items"]["shared_context/rules/python_clean_code.md"]
    assert ctx_item["exists"] is True
    assert "# PEP 8 Rules" in ctx_item["content"]

    # Step 1 has no context files so artifacts should not have loaded_context
    step1 = state.step_states[1]
    assert "loaded_context" not in step1.artifacts

    # Check stdout capture
    captured = capsys.readouterr()
    assert "📂 Arquivos de Contexto: shared_context/rules/python_clean_code.md" in captured.out
    assert "### 📂 Contexto Injetado Automático" in captured.out
    assert "Use snake_case" in captured.out

