import os
from typing import List
import yaml
from pydantic import BaseModel, Field, ValidationError


class AgentStep(BaseModel):
    name: str
    description: str
    agent: str
    context_files: List[str] = Field(default_factory=list)
    expected_output: str
    approval_required: bool = False


class PipelineProfile(BaseModel):
    id: str
    name: str
    description: str
    steps: List[AgentStep]


def parse_pipeline(filepath: str) -> PipelineProfile:
    """Parses a YAML pipeline file and validates it against PipelineProfile schema.

    Args:
        filepath: Path to the YAML profile file.

    Returns:
        PipelineProfile: Validated pipeline profile instance.

    Raises:
        FileNotFoundError: If the file does not exist on disk.
        ValueError: If YAML syntax is invalid or top-level content is not a mapping.
        ValidationError: If schema validation fails.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Profile file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in '{filepath}': {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML content in '{filepath}': expected a dictionary/mapping")

    return PipelineProfile(**data)


def load_profile(profile_id: str, profiles_dir: str = "profiles") -> PipelineProfile:
    """Loads a PipelineProfile by ID from the specified profiles directory.

    Checks for '.yml' and '.yaml' extensions in the profiles directory.

    Args:
        profile_id: Profile identifier (e.g., 'data_engineering').
        profiles_dir: Directory where profile files are located.

    Returns:
        PipelineProfile: Validated pipeline profile instance.
    """
    filepath_yml = os.path.join(profiles_dir, f"{profile_id}.yml")
    filepath_yaml = os.path.join(profiles_dir, f"{profile_id}.yaml")

    if os.path.isfile(filepath_yml):
        filepath = filepath_yml
    elif os.path.isfile(filepath_yaml):
        filepath = filepath_yaml
    else:
        filepath = filepath_yml  # Default path for FileNotFoundError in parse_pipeline

    return parse_pipeline(filepath)

