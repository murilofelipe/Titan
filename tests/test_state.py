import os
import json
import pytest
from core.state import StateManager, StepStatus, PipelineState, StepState
from core.parser import AgentStep


def test_step_status_enum():
    assert StepStatus.PENDING == "PENDING"
    assert StepStatus.IN_PROGRESS == "IN_PROGRESS"
    assert StepStatus.COMPLETED == "COMPLETED"
    assert StepStatus.FAILED == "FAILED"
    assert StepStatus.WAITING_APPROVAL == "WAITING_APPROVAL"


def test_state_initialization_and_persistence(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "test_profile"
    steps = ["Step 1", "Step 2", "Step 3"]

    state = manager.initialize_state(profile_id, steps)
    assert state.profile_id == profile_id
    assert state.status == "PENDING"
    assert state.current_step_index == 0
    assert len(state.step_states) == 3
    assert state.step_states[0].step_name == "Step 1"
    assert state.step_states[0].status == StepStatus.PENDING

    # Check file was saved
    filepath = manager.get_state_filepath(profile_id)
    assert os.path.exists(filepath)

    # Load state from disk
    loaded_state = manager.load_state(profile_id)
    assert loaded_state is not None
    assert loaded_state.profile_id == profile_id
    assert len(loaded_state.step_states) == 3
    assert loaded_state.step_states[1].step_name == "Step 2"


def test_state_initialization_with_agent_steps(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    agent_step = AgentStep(
        name="Ingest Data",
        description="Ingest RAW data",
        agent="data_engineer",
        expected_output="data.csv"
    )
    state = manager.initialize_state("agent_profile", [agent_step])
    assert len(state.step_states) == 1
    assert state.step_states[0].step_name == "Ingest Data"


def test_step_status_updates(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "update_test"
    steps = ["Step A", "Step B"]

    manager.initialize_state(profile_id, steps)

    # Update step 0 to IN_PROGRESS
    state1 = manager.update_step_status(
        profile_id, 0, StepStatus.IN_PROGRESS, notes="Starting step A"
    )
    assert state1.step_states[0].status == StepStatus.IN_PROGRESS
    assert state1.step_states[0].started_at is not None
    assert state1.step_states[0].notes == "Starting step A"
    assert state1.status == "IN_PROGRESS"
    assert state1.current_step_index == 0

    # Update step 0 to COMPLETED
    state2 = manager.update_step_status(
        profile_id, 0, StepStatus.COMPLETED, notes="Completed step A"
    )
    assert state2.step_states[0].status == StepStatus.COMPLETED
    assert state2.step_states[0].completed_at is not None
    assert state2.current_step_index == 1
    assert state2.status == "IN_PROGRESS"

    # Update step 1 to COMPLETED
    state3 = manager.update_step_status(
        profile_id, 1, StepStatus.COMPLETED
    )
    assert state3.step_states[1].status == StepStatus.COMPLETED
    assert state3.status == "COMPLETED"
    assert state3.current_step_index == 2


def test_artifact_passing(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "artifact_test"
    steps = ["Step 1", "Step 2"]

    manager.initialize_state(profile_id, steps)

    # Set artifact globally
    manager.set_artifact(profile_id, "dataset_path", "/data/raw.csv")
    assert manager.get_artifact(profile_id, "dataset_path") == "/data/raw.csv"

    # Pass artifact via step status update
    manager.update_step_status(
        profile_id,
        0,
        StepStatus.COMPLETED,
        artifacts={"processed_count": 100}
    )
    assert manager.get_artifact(profile_id, "processed_count") == 100

    loaded = manager.load_state(profile_id)
    assert loaded.step_states[0].artifacts["processed_count"] == 100
    assert loaded.artifacts["processed_count"] == 100


def test_get_resume_step(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "resume_test"
    steps = ["Step 0", "Step 1", "Step 2"]

    # Initial state -> resume step is 0
    manager.initialize_state(profile_id, steps)
    assert manager.get_resume_step(profile_id) == 0

    # Step 0 completed -> resume step is 1
    manager.update_step_status(profile_id, 0, StepStatus.COMPLETED)
    assert manager.get_resume_step(profile_id) == 1

    # Step 1 failed -> resume step is 1
    manager.update_step_status(profile_id, 1, StepStatus.FAILED)
    assert manager.get_resume_step(profile_id) == 1

    # Step 1 completed -> resume step is 2
    manager.update_step_status(profile_id, 1, StepStatus.COMPLETED)
    assert manager.get_resume_step(profile_id) == 2

    # Step 2 completed -> resume step is 3
    manager.update_step_status(profile_id, 2, StepStatus.COMPLETED)
    assert manager.get_resume_step(profile_id) == 3


def test_non_existent_profile_resume(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    assert manager.get_resume_step("non_existent") == 0


def test_reset_state(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "reset_test"

    manager.initialize_state(profile_id, ["Step 1"])
    filepath = manager.get_state_filepath(profile_id)
    assert os.path.exists(filepath)

    manager.reset_state(profile_id)
    assert not os.path.exists(filepath)
    assert manager.load_state(profile_id) is None


def test_invalid_updates(tmp_path):
    state_dir = str(tmp_path / "titan_state")
    manager = StateManager(state_dir=state_dir)
    profile_id = "invalid_test"

    with pytest.raises(ValueError):
        manager.update_step_status(profile_id, 0, StepStatus.COMPLETED)

    manager.initialize_state(profile_id, ["Step 1"])
    with pytest.raises(IndexError):
        manager.update_step_status(profile_id, 5, StepStatus.COMPLETED)
