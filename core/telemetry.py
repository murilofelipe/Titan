"""Telemetria de execução — agrega o PipelineState em um resumo legível.

Cobre o que o StateManager já grava por etapa: agente recomendado, duração
(started_at/completed_at) e quem liberou a etapa (auto/humano). Não mede custo
de token nem qualidade da saída do agente.
"""

from typing import Optional

from core.state import PipelineState, StepStatus


def _fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.1f}min"


def render_report(state: PipelineState) -> str:
    """Resumo Markdown da execução de um pipeline."""
    steps = state.step_states
    done = sum(1 for s in steps if s.status == StepStatus.COMPLETED)
    auto = sum(1 for s in steps if s.advanced_by == "auto")
    human = sum(1 for s in steps if s.advanced_by == "human")
    durations = [s.duration_seconds for s in steps if s.duration_seconds is not None]
    total = sum(durations) if durations else None

    lines = [
        f"# Telemetria — {state.profile_id}",
        "",
        f"**Placar:** {done}/{len(steps)} etapas concluídas · "
        f"{human} liberadas por humano · {auto} automáticas · "
        f"tempo total {_fmt_duration(total)}",
        "",
        "> Cobre agente, duração e quem liberou cada etapa. Não mede custo de "
        "token nem qualidade da saída do agente.",
        "",
        "## Etapas",
        "",
        "| # | Etapa | Agente | Status | Duração | Liberada por |",
        "|---|---|---|---|---|---|",
    ]
    for s in steps:
        lines.append(
            f"| {s.step_index + 1} | {s.step_name} | {s.agent or '—'} | "
            f"{s.status} | {_fmt_duration(s.duration_seconds)} | {s.advanced_by or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)
