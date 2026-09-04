"""AI Work Classifier for Titan Core.

Classifies input prompts or intents into Titan pipeline profile IDs.

Estratégia: scoring por keyword (sem ML). Cada perfil tem um dicionário de
termos de domínio; o vencedor só é retornado se a diferença normalizada para o
segundo colocado passar do limiar de confiança E o `.yml` do perfil existir.
Caso contrário cai no default (ou pergunta, quando `interactive=True`).
"""

import os
from typing import Dict, List, Optional
import click
import yaml

DEFAULT_PROFILE = "data_engineering"

# Margem mínima (score_best - score_2nd) / score_total para aceitar o vencedor.
CONFIDENCE_THRESHOLD = 0.25

# Keywords de domínio por perfil. Os perfis mobile/embedded/ai_ml/game ainda não
# têm `.yml` (stories 2.4–2.7); as keywords ficam dormentes até lá — o gate de
# disponibilidade em classify_work impede um retorno para perfil inexistente.
PROFILE_KEYWORDS: Dict[str, List[str]] = {
    "data_engineering": [
        "data engineering", "data_engineering", "etl", "dbt", "sql", "pipeline",
        "data pipeline", "extract", "extraction", "transform", "transformation",
        "data warehouse", "lakehouse",
    ],
    "backend_clean_arch": [
        "backend", "backend_clean_arch", "api", "clean architecture", "clean arch",
        "ddd", "domain driven", "domain-driven", "microservices", "microservice",
        "fastapi", "rest api", "rest",
    ],
    "mobile_android": [
        "android", "jetpack compose", "compose", "kotlin", "mvvm",
        "play store", "activity", "fragment", "room database", "offline-first",
    ],
    "embedded": [
        "embarcado", "embedded", "firmware", "datasheet", "microcontrolador",
        "microcontroller", "esp32", "arduino", "stm32", "rtos", "gpio", "i2c",
        "spi", "flash da placa",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "model training", "treinamento de modelo",
        "pytorch", "tensorflow", "fine-tuning", "fine tuning", "rede neural",
        "neural network", "training dataset",
    ],
    "game": [
        "game", "jogo", "godot", "unity", "unreal", "game loop", "sprite",
        "gameplay", "physics engine",
    ],
}


def get_available_profiles(profiles_dir: str = "profiles") -> List[str]:
    """Scan profiles directory for valid YAML profiles and return sorted profile IDs."""
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
                profile_id = os.path.splitext(filename)[0]

            if profile_id:
                profiles.add(profile_id)

    return sorted(list(profiles))


def _kw_weight(kw: str) -> int:
    """Frase (com espaço/underscore) pesa 2; termo único pesa 1."""
    return 2 if " " in kw or "_" in kw else 1


def score_profiles(cleaned_prompt: str) -> Dict[str, int]:
    """Score bruto por perfil para um prompt já normalizado (lower/strip)."""
    scores: Dict[str, int] = {}
    for profile_id, keywords in PROFILE_KEYWORDS.items():
        score = sum(_kw_weight(kw) for kw in keywords if kw in cleaned_prompt)
        if score:
            scores[profile_id] = score
    return scores


def _ask_profile(available: List[str], default_profile: str) -> str:
    """Fallback interativo — usa click.prompt (não passa por builtins.input)."""
    if not available:
        return default_profile
    choice_default = default_profile if default_profile in available else available[0]
    return click.prompt(
        "Não consegui classificar o pedido com confiança. Qual perfil usar?",
        type=click.Choice(available),
        default=choice_default,
        show_choices=True,
    )


def classify_work(
    prompt_or_intent: Optional[str] = None,
    profiles_dir: str = "profiles",
    default_profile: str = DEFAULT_PROFILE,
    interactive: bool = False,
    **kwargs,
) -> str:
    """Classify input prompt or intent into a Titan pipeline profile ID.

    Args:
        prompt_or_intent: Prompt string or intent description.
        profiles_dir: Path to profiles directory.
        default_profile: Fallback profile ID if unrecognized or ambiguous.
        interactive: Se True, pergunta o perfil (click.prompt) quando a
            confiança fica abaixo do limiar em vez de cair no default.
        **kwargs: Aceita 'prompt' como alias de prompt_or_intent.

    Returns:
        Profile ID string.
    """
    if prompt_or_intent is None and "prompt" in kwargs:
        prompt_or_intent = kwargs["prompt"]

    if not prompt_or_intent or not isinstance(prompt_or_intent, str):
        return default_profile

    cleaned_prompt = prompt_or_intent.strip().lower()
    if not cleaned_prompt:
        return default_profile

    available_profiles = get_available_profiles(profiles_dir)

    # 1. Match direto de ID de perfil.
    for p_id in available_profiles:
        p_id_lower = p_id.lower()
        if cleaned_prompt == p_id_lower or cleaned_prompt == p_id_lower.replace("_", " "):
            return p_id

    # 2. Scoring por keyword com limiar de confiança.
    scores = score_profiles(cleaned_prompt)
    if scores:
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best_id, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0
        total = sum(scores.values())
        confidence = (best_score - second_score) / total

        if confidence >= CONFIDENCE_THRESHOLD:
            if best_id in available_profiles:
                return best_id
            click.echo(
                f"⚠️  Pedido parece '{best_id}', mas esse perfil ainda não foi "
                f"implementado. Usando '{default_profile}'."
            )

    # 3. Baixa confiança / perfil ainda não implementado / sem keyword.
    if interactive:
        return _ask_profile(available_profiles, default_profile)
    return default_profile
