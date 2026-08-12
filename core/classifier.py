"""AI Work Classifier for Titan Core.

Classifies input prompts or intents into Titan pipeline profile IDs
(e.g., data_engineering, backend_clean_arch).
"""

import os
from typing import List, Optional
import yaml

DEFAULT_PROFILE = "data_engineering"

# Keywords for Data Engineering classification
DATA_ENGINEERING_KEYWORDS = [
    "data engineering",
    "data_engineering",
    "etl",
    "dbt",
    "sql",
    "pipeline",
    "data pipeline",
    "extract",
    "extraction",
    "transform",
    "transformation",
    "data warehouse",
    "lakehouse",
]

# Keywords for Backend Clean Architecture classification
BACKEND_KEYWORDS = [
    "backend",
    "backend_clean_arch",
    "api",
    "clean architecture",
    "clean arch",
    "ddd",
    "domain driven",
    "domain-driven",
    "microservices",
    "microservice",
    "fastapi",
    "rest api",
    "rest",
]


def get_available_profiles(profiles_dir: str = "profiles") -> List[str]:
    """Scan profiles directory for valid YAML profiles and return list of profile IDs.

    Args:
        profiles_dir: Path to directory containing profile YAML files.

    Returns:
        List of profile ID strings, sorted alphabetically.
    """
    if not os.path.exists(profiles_dir) or not os.path.isdir(profiles_dir):
        return []

    profiles = set()
    for filename in os.listdir(profiles_dir):
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            file_path = os.path.join(profiles_dir, filename)
            profile_id = None
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if isinstance(content, dict) and "id" in content:
                        profile_id = str(content["id"]).strip()
            except Exception:
                pass

            if not profile_id:
                # Fallback to filename stem
                profile_id = os.path.splitext(filename)[0]

            if profile_id:
                profiles.add(profile_id)

    return sorted(list(profiles))


def classify_work(
    prompt_or_intent: Optional[str] = None,
    profiles_dir: str = "profiles",
    default_profile: str = DEFAULT_PROFILE,
    **kwargs,
) -> str:
    """Classify input prompt or intent into a Titan pipeline profile ID.

    Args:
        prompt_or_intent: Prompt string or intent description.
        profiles_dir: Path to profiles directory.
        default_profile: Fallback profile ID if unrecognized or ambiguous.
        **kwargs: Supports 'prompt' argument name for compatibility.

    Returns:
        Profile ID string (e.g., 'data_engineering' or 'backend_clean_arch').
    """
    # Accept 'prompt' keyword argument if passed instead of prompt_or_intent
    if prompt_or_intent is None and "prompt" in kwargs:
        prompt_or_intent = kwargs["prompt"]

    if not prompt_or_intent or not isinstance(prompt_or_intent, str):
        return default_profile

    cleaned_prompt = prompt_or_intent.strip().lower()
    if not cleaned_prompt:
        return default_profile

    # 1. Direct profile ID match check
    available_profiles = get_available_profiles(profiles_dir)
    for p_id in available_profiles:
        p_id_lower = p_id.lower()
        if cleaned_prompt == p_id_lower or cleaned_prompt == p_id_lower.replace("_", " "):
            return p_id

    # 2. Keyword score matching
    de_score = 0
    for kw in DATA_ENGINEERING_KEYWORDS:
        if kw in cleaned_prompt:
            # Multi-word phrase gets higher weight
            de_score += 2 if " " in kw or "_" in kw else 1

    backend_score = 0
    for kw in BACKEND_KEYWORDS:
        if kw in cleaned_prompt:
            backend_score += 2 if " " in kw or "_" in kw else 1

    if backend_score > de_score and backend_score > 0:
        return "backend_clean_arch"
    elif de_score > backend_score and de_score > 0:
        return "data_engineering"

    # 3. Fallback for unrecognized or ambiguous inputs
    return default_profile
