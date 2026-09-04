import os
import json
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_APPROVAL = "WAITING_APPROVAL"


class StepState(BaseModel):
    step_index: int
    step_name: str
    status: StepStatus = StepStatus.PENDING
    agent: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    advanced_by: Optional[str] = None  # "auto" | "human" — quem liberou a etapa
    approved_by: Optional[str] = None   # quem registrou a aprovação do gate (S4.1)
    approved_at: Optional[str] = None
    review_cycles: int = 0              # rejeições já acumuladas nesta etapa de review (S4.2)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at or not self.completed_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
        except ValueError:
            return None
        return (end - start).total_seconds()


class PipelineState(BaseModel):
    profile_id: str
    status: str = "PENDING"
    current_step_index: int = 0
    step_states: List[StepState] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StateManager:
    def __init__(self, state_dir: str = ".titan_state"):
        self.state_dir = state_dir

    def get_state_filepath(self, profile_id: str) -> str:
        return os.path.join(self.state_dir, f"{profile_id}.json")

    def initialize_state(self, profile_id: str, steps: List[Any]) -> PipelineState:
        step_states = []
        for i, step in enumerate(steps):
            if isinstance(step, str):
                name = step
            elif hasattr(step, "name"):
                name = step.name
            elif isinstance(step, dict) and "name" in step:
                name = step["name"]
            else:
                name = str(step)
            step_states.append(
                StepState(
                    step_index=i,
                    step_name=name,
                    agent=getattr(step, "agent", None),
                    status=StepStatus.PENDING
                )
            )
        state = PipelineState(
            profile_id=profile_id,
            status="PENDING",
            current_step_index=0,
            step_states=step_states,
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        self.save_state(state)
        return state

    def load_state(self, profile_id: str) -> Optional[PipelineState]:
        filepath = self.get_state_filepath(profile_id)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return PipelineState.model_validate_json(content)
        except Exception:
            return None

    def save_state(self, state: PipelineState) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        filepath = self.get_state_filepath(state.profile_id)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))

    def update_step_status(
        self,
        profile_id: str,
        step_index: int,
        status: StepStatus,
        notes: Optional[str] = None,
        artifacts: Optional[Dict[str, Any]] = None,
        advanced_by: Optional[str] = None
    ) -> PipelineState:
        state = self.load_state(profile_id)
        if state is None:
            raise ValueError(f"No state found for profile '{profile_id}'")

        if step_index < 0 or step_index >= len(state.step_states):
            raise IndexError(f"Step index {step_index} out of range for profile '{profile_id}'")

        if isinstance(status, str):
            status = StepStatus(status)

        step = state.step_states[step_index]
        step.status = status
        now_iso = datetime.now(timezone.utc).isoformat()

        if status == StepStatus.IN_PROGRESS and not step.started_at:
            step.started_at = now_iso
        elif status in (StepStatus.COMPLETED, StepStatus.FAILED) and not step.completed_at:
            if not step.started_at:
                step.started_at = now_iso
            step.completed_at = now_iso

        if notes is not None:
            step.notes = notes

        if advanced_by is not None:
            step.advanced_by = advanced_by

        if artifacts:
            step.artifacts.update(artifacts)
            state.artifacts.update(artifacts)

        if status == StepStatus.COMPLETED:
            next_index = step_index + 1
            state.current_step_index = min(next_index, len(state.step_states))
            if all(s.status == StepStatus.COMPLETED for s in state.step_states):
                state.status = "COMPLETED"
            else:
                state.status = "IN_PROGRESS"
        elif status == StepStatus.IN_PROGRESS:
            state.current_step_index = step_index
            state.status = "IN_PROGRESS"
        elif status == StepStatus.FAILED:
            state.status = "FAILED"
        elif status == StepStatus.WAITING_APPROVAL:
            state.status = "WAITING_APPROVAL"

        self.save_state(state)
        return state

    def approve_step(self, profile_id: str, step_index: int, approver: str) -> PipelineState:
        """Registra a aprovação humana de um gate (S4.1). Não avança sozinha — o
        `run --resume` é quem libera a etapa depois de aprovada."""
        state = self.load_state(profile_id)
        if state is None:
            raise ValueError(f"No state found for profile '{profile_id}'")
        if step_index < 0 or step_index >= len(state.step_states):
            raise IndexError(f"Step index {step_index} out of range for profile '{profile_id}'")
        step = state.step_states[step_index]
        step.approved_by = approver
        step.approved_at = datetime.now(timezone.utc).isoformat()
        self.save_state(state)
        return state

    def register_verdict(
        self,
        profile_id: str,
        review_step_index: int,
        approved: bool,
        return_to_index: int,
        max_cycles: int = 3,
        reason: Optional[str] = None,
    ) -> PipelineState:
        """Registra o veredito do revisor (S4.2).

        APROVA: registra a aprovação do gate (o `run --resume` conclui a etapa).
        REJEITA: incrementa o contador de ciclos e devolve as etapas
        `return_to_index..review_step_index` para PENDING. Estourando o teto, a
        etapa de review vira FAILED (precisa de humano)."""
        state = self.load_state(profile_id)
        if state is None:
            raise ValueError(f"No state found for profile '{profile_id}'")
        if not (0 <= review_step_index < len(state.step_states)):
            raise IndexError(f"Step index {review_step_index} out of range")

        review = state.step_states[review_step_index]

        if approved:
            review.approved_by = review.approved_by or "revisor"
            review.approved_at = datetime.now(timezone.utc).isoformat()
            review.notes = reason or review.notes
            self.save_state(state)
            return state

        review.review_cycles += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        if review.review_cycles > max_cycles:
            review.status = StepStatus.FAILED
            review.completed_at = now_iso
            review.notes = f"REJEITA x{review.review_cycles} — teto {max_cycles} estourado. {reason or ''}".strip()
            state.status = "FAILED"
            self.save_state(state)
            return state

        review.notes = f"REJEITA (ciclo {review.review_cycles}): {reason or 'sem motivo'}"
        for i in range(return_to_index, review_step_index + 1):
            s = state.step_states[i]
            s.status = StepStatus.PENDING
            s.started_at = None
            s.completed_at = None
            s.advanced_by = None
            if i != review_step_index:
                s.review_cycles = 0
        state.current_step_index = return_to_index
        state.status = "IN_PROGRESS"
        self.save_state(state)
        return state

    def set_artifact(self, profile_id: str, key: str, value: Any) -> PipelineState:
        state = self.load_state(profile_id)
        if state is None:
            raise ValueError(f"No state found for profile '{profile_id}'")
        state.artifacts[key] = value
        self.save_state(state)
        return state

    def get_artifact(self, profile_id: str, key: str) -> Any:
        state = self.load_state(profile_id)
        if state is None:
            return None
        return state.artifacts.get(key)

    def get_resume_step(self, profile_id: str) -> int:
        state = self.load_state(profile_id)
        if not state or not state.step_states:
            return 0
        for step in state.step_states:
            if step.status != StepStatus.COMPLETED:
                return step.step_index
        return len(state.step_states)

    def reset_state(self, profile_id: str) -> None:
        filepath = self.get_state_filepath(profile_id)
        if os.path.exists(filepath):
            os.remove(filepath)
