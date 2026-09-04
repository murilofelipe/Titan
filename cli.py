import os

import click
from core.classifier import get_available_profiles
from core.parser import load_profile
from core.orchestrator import Orchestrator
from core.state import StateManager
from core.telemetry import render_report


@click.group()
def cli():
    """Titan / HAL - Orquestrador Agêntico"""
    pass


@cli.command()
@click.argument("profile_id_or_prompt", required=False, default="data_engineering")
@click.option("--auto", "-y", is_flag=True, help="Auto-approve all steps non-interactively")
@click.option("--resume", is_flag=True, help="Resume pipeline from last incomplete step")
@click.option("--reset", is_flag=True, help="Reset pipeline execution state before running")
def run(profile_id_or_prompt, auto, resume, reset):
    """Executa um pipeline de desenvolvimento a partir do ID do perfil ou prompt de intenção."""
    orchestrator = Orchestrator()
    orchestrator.run_pipeline(
        profile_id_or_prompt=profile_id_or_prompt,
        auto_approve=auto,
        resume=resume,
        reset=reset,
    )


@cli.command(name="list")
def list_profiles():
    """Lista todos os perfis YAML disponíveis no diretório profiles/ com nome e descrição."""
    available_ids = get_available_profiles("profiles")
    if not available_ids:
        click.echo("Nenhum perfil encontrado.")
        return

    click.echo("📋 Perfis Disponíveis:")
    click.echo("-" * 50)
    for p_id in available_ids:
        try:
            profile = load_profile(p_id, profiles_dir="profiles")
            click.echo(f"• {profile.id} ({profile.name})")
            click.echo(f"  Descrição: {profile.description}")
        except Exception as e:
            click.echo(f"• {p_id} (Erro ao carregar: {e})")
    click.echo("-" * 50)


@cli.command()
@click.argument("profile_id", required=False, default="data_engineering")
def status(profile_id):
    """Exibe o estado atual de execução de um perfil usando StateManager."""
    state_manager = StateManager()
    state = state_manager.load_state(profile_id)
    if not state:
        click.echo(f"Nenhum estado encontrado para o perfil '{profile_id}'.")
        return

    click.echo(f"📊 Estado do Pipeline: {state.profile_id}")
    click.echo(f"Status Geral: {state.status}")
    click.echo(f"Etapa Atual: {state.current_step_index}/{len(state.step_states)}")
    click.echo("-" * 50)
    for step in state.step_states:
        agent = f" · {step.agent}" if step.agent else ""
        dur = step.duration_seconds
        dur_txt = f" · {dur:.0f}s" if dur is not None else ""
        by = f" · por {step.advanced_by}" if step.advanced_by else ""
        click.echo(f"  [{step.step_index + 1}] {step.step_name}: {step.status}{agent}{dur_txt}{by}")
    click.echo("-" * 50)


@cli.command()
@click.argument("profile_id", required=False, default="data_engineering")
@click.option("--output", "-o", default=None, help="Caminho do .md (padrão: .reports/telemetria-<perfil>.md)")
def report(profile_id, output):
    """Gera o relatório de telemetria de execução em Markdown (arquivo + stdout)."""
    state = StateManager().load_state(profile_id)
    if not state:
        click.echo(f"Nenhum estado encontrado para o perfil '{profile_id}'.")
        return

    md = render_report(state)
    path = output or os.path.join(".reports", f"telemetria-{profile_id}.md")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)

    click.echo(md)
    click.echo(f"\n📄 Relatório salvo em: {path}")


if __name__ == "__main__":
    cli()

