from click.testing import CliRunner
from cli import cli
from core.state import StateManager


def test_cli_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Perfis Disponíveis" in result.output
    assert "data_engineering" in result.output
    assert "backend_clean_arch" in result.output


def test_cli_status_no_state(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")
    monkeypatch.setattr("core.state.StateManager.__init__", lambda self, state_dir=state_dir: setattr(self, 'state_dir', state_dir))

    runner = CliRunner()
    result = runner.invoke(cli, ["status", "non_existent_profile"])
    assert result.exit_code == 0
    assert "Nenhum estado encontrado" in result.output


def test_cli_run_auto_and_status(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")

    # Patch StateManager default state_dir to test isolated location
    original_init = StateManager.__init__
    def patched_init(self, state_dir_arg=state_dir):
        original_init(self, state_dir=state_dir_arg)

    monkeypatch.setattr("core.state.StateManager.__init__", patched_init)
    monkeypatch.setattr("core.orchestrator.StateManager.__init__", patched_init)

    runner = CliRunner()

    # Test run --auto
    run_result = runner.invoke(cli, ["run", "data_engineering", "--auto"])
    assert run_result.exit_code == 0
    assert "Iniciando Pipeline" in run_result.output
    assert "Pipeline concluído com sucesso!" in run_result.output

    # Test status after run
    status_result = runner.invoke(cli, ["status", "data_engineering"])
    assert status_result.exit_code == 0
    assert "Estado do Pipeline: data_engineering" in status_result.output
    assert "COMPLETED" in status_result.output


def test_cli_run_flags(tmp_path, monkeypatch):
    state_dir = str(tmp_path / "titan_state")

    original_init = StateManager.__init__
    def patched_init(self, state_dir_arg=state_dir):
        original_init(self, state_dir=state_dir_arg)

    monkeypatch.setattr("core.state.StateManager.__init__", patched_init)
    monkeypatch.setattr("core.orchestrator.StateManager.__init__", patched_init)

    runner = CliRunner()

    # Run with prompt intent and --auto
    res1 = runner.invoke(cli, ["run", "backend clean architecture API", "-y"])
    assert res1.exit_code == 0
    assert "Pipeline concluído com sucesso!" in res1.output

    # Run with --resume flag
    res2 = runner.invoke(cli, ["run", "backend_clean_arch", "--auto", "--resume"])
    assert res2.exit_code == 0
    assert "Pipeline concluído com sucesso!" in res2.output

    # Run with --reset flag
    res3 = runner.invoke(cli, ["run", "backend_clean_arch", "--auto", "--reset"])
    assert res3.exit_code == 0
    assert "Pipeline concluído com sucesso!" in res3.output
