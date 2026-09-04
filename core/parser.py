import os
from typing import List, Literal, Optional
import yaml
from pydantic import BaseModel, Field, ValidationError


class StepValidation(BaseModel):
    """Checagem automática do resultado de uma etapa antes de liberar a próxima (S4.3)."""
    type: Literal["file_exists", "command_zero", "glob_nonempty"]
    path: Optional[str] = None      # file_exists
    cmd: Optional[List[str]] = None  # command_zero — lista de args (shell=False)
    pattern: Optional[str] = None   # glob_nonempty


class AgentStep(BaseModel):
    name: str
    description: str
    agent: str
    context_files: List[str] = Field(default_factory=list)
    expected_output: str
    approval_required: bool = False
    validation: List[StepValidation] = Field(default_factory=list)


class PipelineProfile(BaseModel):
    id: str
    name: str
    description: str
    steps: List[AgentStep]


class AgentRole(BaseModel):
    name: str
    role: str
    strength: str = ""
    when: str = ""
    instructions: str = ""


class AgentRegistry(BaseModel):
    agents: List[AgentRole]

    def names(self) -> List[str]:
        return [a.name for a in self.agents]

    def get(self, name: str) -> "AgentRole | None":
        return next((a for a in self.agents if a.name == name), None)


AGENT_REGISTRY_PATH = os.path.join("shared_context", "agents.yml")


def load_agent_registry(path: str = AGENT_REGISTRY_PATH) -> AgentRegistry:
    """Carrega o catálogo de agentes (shared_context/agents.yml)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Agent registry not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid agent registry in '{path}': expected a mapping")
    return AgentRegistry(**data)


def validate_profile_agents(
    profile: PipelineProfile, registry: "AgentRegistry | None" = None
) -> List[str]:
    """Retorna a lista de `agent:` do profile que não estão no registry (vazia = ok)."""
    if registry is None:
        registry = load_agent_registry()
    known = set(registry.names())
    return sorted({s.agent for s in profile.steps if s.agent not in known})


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

