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
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


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
        artifacts: Optional[Dict[str, Any]] = None
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
