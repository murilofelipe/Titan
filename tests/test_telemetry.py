"""Testes da telemetria de execução (core/telemetry.py + campos em StepState)."""

from click.testing import CliRunner

from cli import cli
from core.orchestrator import Orchestrator
from core.parser import AgentStep
from core.state import StateManager, StepStatus
from core.telemetry import render_report


def _run(tmp_path, monkeypatch, auto):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    sm = StateManager(state_dir=str(tmp_path / "st"))
    orch = Orchestrator(profiles_dir="profiles", state_manager=sm)
    orch.run_pipeline("data_engineering", auto_approve=auto)
    return sm.load_state("data_engineering")


def test_step_records_agent_and_advanced_by(tmp_path, monkeypatch):
    state = _run(tmp_path, monkeypatch, auto=True)
    assert all(s.advanced_by == "auto" for s in state.step_states)
    assert state.step_states[0].agent == "Claude Code"


def test_step_advanced_by_human_interactive(tmp_path, monkeypatch):
    state = _run(tmp_path, monkeypatch, auto=False)
    assert all(s.advanced_by == "human" for s in state.step_states)


def test_duration_seconds_none_until_completed(tmp_path):
    sm = StateManager(state_dir=str(tmp_path / "st"))
    step = AgentStep(name="X", description="d", agent="Claude Code", expected_output="o")
    sm.initialize_state("p", [step])
    assert sm.load_state("p").step_states[0].duration_seconds is None
    sm.update_step_status("p", 0, StepStatus.IN_PROGRESS)
    sm.update_step_status("p", 0, StepStatus.COMPLETED)
    assert sm.load_state("p").step_states[0].duration_seconds is not None


def test_cli_report_bare_output_filename(tmp_path, monkeypatch):
    """`report -o nome.md` (sem diretório) não pode estourar em os.makedirs."""
    monkeypatch.chdir(tmp_path)
    StateManager().initialize_state("p", ["a", "b"])
    result = CliRunner().invoke(cli, ["report", "p", "-o", "resumo.md"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "resumo.md").exists()


def test_render_report_markdown(tmp_path, monkeypatch):
    state = _run(tmp_path, monkeypatch, auto=True)
    md = render_report(state)
    assert md.startswith("# Telemetria — data_engineering")
    assert "**Placar:**" in md
    assert "| # | Etapa | Agente |" in md
    assert "Claude Code" in md
