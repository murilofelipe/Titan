import os

import click
from core.classifier import get_available_profiles
from core.parser import load_profile, load_agent_registry, validate_profile_agents
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

    registry = load_agent_registry()
    click.echo("📋 Perfis Disponíveis:")
    click.echo("-" * 50)
    for p_id in available_ids:
        try:
            profile = load_profile(p_id, profiles_dir="profiles")
            click.echo(f"• {profile.id} ({profile.name})")
            click.echo(f"  Descrição: {profile.description}")
            unknown = validate_profile_agents(profile, registry)
            if unknown:
                click.echo(f"  ⚠️  Agentes fora do registry: {', '.join(unknown)}")
        except Exception as e:
            click.echo(f"• {p_id} (Erro ao carregar: {e})")
    click.echo("-" * 50)


@cli.command(name="agents")
def list_agents():
    """Lista o registry de agentes (papel, ponto forte, quando usar)."""
    for a in load_agent_registry().agents:
        click.echo(f"• {a.name} — {a.role}")
        click.echo(f"  Forte em: {a.strength}")
        click.echo(f"  Quando: {a.when}")


@cli.command()
@click.argument("profile_id")
@click.argument("step_number", type=int)
def approve(profile_id, step_number):
    """Aprova um gate (STEP_NUMBER é 1-based). Depois rode `titan run <perfil> --resume`."""
    sm = StateManager()
    state = sm.load_state(profile_id)
    if not state:
        click.echo(f"Nenhum estado encontrado para o perfil '{profile_id}'.")
        return
    idx = step_number - 1
    if idx < 0 or idx >= len(state.step_states):
        click.echo(f"Etapa {step_number} fora do intervalo (1..{len(state.step_states)}).")
        return
    approver = os.environ.get("USER") or "humano"
    sm.approve_step(profile_id, idx, approver)
    click.echo(f"✅ Etapa {step_number} aprovada por {approver}. Rode: titan run {profile_id} --resume")


@cli.command()
@click.argument("profile_id")
@click.argument("step_number", type=int)
@click.argument("verdict", type=click.Choice(["aprova", "rejeita"], case_sensitive=False))
@click.option("--motivo", default=None, help="Motivo da rejeição (vai para as notas da etapa).")
def verdict(profile_id, step_number, verdict, motivo):
    """Registra o veredito do revisor numa etapa de review (S4.2).

    `aprova` libera o gate; `rejeita` devolve o pipeline para a etapa de
    implementação (até `max_review_cycles`). Depois rode `titan run <perfil> --resume`.
    """
    sm = StateManager()
    state = sm.load_state(profile_id)
    if not state:
        click.echo(f"Nenhum estado encontrado para o perfil '{profile_id}'.")
        return
    idx = step_number - 1
    if idx < 0 or idx >= len(state.step_states):
        click.echo(f"Etapa {step_number} fora do intervalo (1..{len(state.step_states)}).")
        return
    profile = load_profile(profile_id, profiles_dir="profiles")
    try:
        return_to = profile.reject_target_index(idx)
    except ValueError as e:
        click.echo(f"Erro: {e}")
        return
    approved = verdict.lower() == "aprova"
    new = sm.register_verdict(profile_id, idx, approved, return_to, profile.max_review_cycles, motivo)
    step = new.step_states[idx]
    if approved:
        click.echo(f"✅ Etapa {step_number} aprovada pelo revisor. Rode: titan run {profile_id} --resume")
    elif step.status == "FAILED":
        click.echo(f"⛔ Etapa {step_number} REJEITA {step.review_cycles}x — teto {profile.max_review_cycles} estourado. Precisa de intervenção humana.")
    else:
        rt = new.step_states[return_to].step_name
        click.echo(f"🔁 Rejeitada (ciclo {step.review_cycles}). Pipeline volta para '{rt}'. Rode: titan run {profile_id} --resume")


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
    waiting = []
    for step in state.step_states:
        agent = f" · {step.agent}" if step.agent else ""
        dur = step.duration_seconds
        dur_txt = f" · {dur:.0f}s" if dur is not None else ""
        by = f" · por {step.advanced_by}" if step.advanced_by else ""
        appr = f" · aprovada por {step.approved_by}" if step.approved_by else ""
        cyc = f" · review rejeitado {step.review_cycles}x" if step.review_cycles else ""
        click.echo(f"  [{step.step_index + 1}] {step.step_name}: {step.status}{agent}{dur_txt}{by}{appr}{cyc}")
        if step.status == "WAITING_APPROVAL" and not step.approved_by:
            waiting.append(step.step_index + 1)
    click.echo("-" * 50)
    if waiting:
        nums = ", ".join(str(n) for n in waiting)
        click.echo(f"⏸️  Aguardando aprovação: etapa(s) {nums} — rode `titan approve {state.profile_id} <n>`")


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

