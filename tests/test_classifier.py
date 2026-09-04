"""Unit tests for AI Work Classifier (core/classifier.py)."""

import os
import pytest
from core.classifier import (
    classify_work,
    get_available_profiles,
    DEFAULT_PROFILE,
)


def test_get_available_profiles_default_dir():
    """Verify get_available_profiles returns existing profiles from default directory."""
    profiles = get_available_profiles("profiles")
    assert isinstance(profiles, list)
    assert "backend_clean_arch" in profiles
    assert "data_engineering" in profiles
    assert profiles == sorted(profiles)


def test_get_available_profiles_non_existent_dir():
    """Verify get_available_profiles returns empty list for non-existent directory."""
    profiles = get_available_profiles("non_existent_directory_xyz")
    assert profiles == []


def test_get_available_profiles_custom_dir(tmp_path):
    """Verify get_available_profiles parses YAML profile IDs correctly."""
    p_dir = tmp_path / "custom_profiles"
    p_dir.mkdir()
    
    yaml_file1 = p_dir / "custom_one.yml"
    yaml_file1.write_text('id: "custom_one"\nname: "Custom One"\n')
    
    yaml_file2 = p_dir / "custom_two.yaml"
    yaml_file2.write_text('id: "custom_two"\nname: "Custom Two"\n')

    profiles = get_available_profiles(str(p_dir))
    assert profiles == ["custom_one", "custom_two"]


def test_classify_work_direct_match():
    """Verify direct profile ID matching (case-insensitive)."""
    assert classify_work("data_engineering") == "data_engineering"
    assert classify_work("backend_clean_arch") == "backend_clean_arch"
    assert classify_work("DATA_ENGINEERING") == "data_engineering"
    assert classify_work("BACKEND_CLEAN_ARCH") == "backend_clean_arch"
    assert classify_work("backend clean arch") == "backend_clean_arch"


def test_classify_work_keyword_data_engineering():
    """Verify classification of prompts with data engineering keywords."""
    assert classify_work("Crie uma pipeline ETL para extração de dados SQL") == "data_engineering"
    assert classify_work("Preciso de um projeto dbt com modelagem para data warehouse") == "data_engineering"
    assert classify_work("Build a data engineering pipeline for ETL") == "data_engineering"
    assert classify_work("Criar scripts de extração e transformação lakehouse") == "data_engineering"


def test_classify_work_keyword_backend():
    """Verify classification of prompts with backend clean architecture keywords."""
    assert classify_work("Construa uma API REST com FastAPI utilizando Clean Architecture e DDD") == "backend_clean_arch"
    assert classify_work("Desenvolva microservices para a camada de backend") == "backend_clean_arch"
    assert classify_work("Setup backend clean arch with domain-driven design") == "backend_clean_arch"
    assert classify_work("Implementar rotas de API em FastAPI") == "backend_clean_arch"


def test_classify_work_fallback_ambiguous_and_unrecognized():
    """Verify fallback behavior for unrecognized or ambiguous prompts."""
    # Unrecognized prompt
    assert classify_work("Faça uma análise genérica sem palavras-chave específicas") == DEFAULT_PROFILE
    assert classify_work("Hello world 123") == DEFAULT_PROFILE

    # Ambiguous prompt with equal weight or conflicting keywords
    assert classify_work("API pipeline ETL dbt microservices") == DEFAULT_PROFILE


def test_classify_work_empty_whitespace_none():
    """Verify handling of empty, whitespace, and None prompts."""
    assert classify_work("") == DEFAULT_PROFILE
    assert classify_work("   ") == DEFAULT_PROFILE
    assert classify_work(None) == DEFAULT_PROFILE


def test_classify_work_never_returns_unavailable_profile():
    """Invariante: nunca devolve perfil que load_profile não conseguiria abrir.

    Hoje 'mobile_android' tem keywords mas não tem .yml -> cai no default.
    Continua válido quando a story 2.4 criar o .yml (aí devolve mobile_android).
    """
    result = classify_work("Build an Android app with Jetpack Compose and MVVM")
    assert result in get_available_profiles("profiles")


def test_classify_work_new_profiles():
    """Perfis 2.4–2.7: agora têm .yml, então o classificador deve acertá-los."""
    assert classify_work("Build an Android app with Jetpack Compose and MVVM") == "mobile_android"
    assert classify_work("firmware para ESP32 lendo datasheet do sensor I2C") == "embedded"
    assert classify_work("treinamento de modelo PyTorch com rede neural") == "ai_ml"
    assert classify_work("desenvolver um jogo na engine Godot com game loop") == "game"


def test_classify_work_interactive_prompts_on_low_confidence(monkeypatch):
    """Com interactive=True e baixa confiança, pergunta o perfil via click.prompt."""
    asked = {}

    def fake_prompt(text, **kwargs):
        asked["called"] = True
        return "backend_clean_arch"

    monkeypatch.setattr("core.classifier.click.prompt", fake_prompt)
    result = classify_work("algo totalmente ambíguo sem termos", interactive=True)
    assert asked.get("called") is True
    assert result == "backend_clean_arch"


def test_classify_work_non_interactive_never_prompts(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("click.prompt não deveria ser chamado")

    monkeypatch.setattr("core.classifier.click.prompt", boom)
    assert classify_work("texto sem palavras-chave") == DEFAULT_PROFILE


def test_classify_work_prompt_kwarg_alias():
    """Verify classify_work supports 'prompt' keyword argument."""
    assert classify_work(prompt="backend_clean_arch") == "backend_clean_arch"
    assert classify_work(prompt="Desenvolver API em FastAPI") == "backend_clean_arch"
    assert classify_work(prompt="Pipeline ETL dbt") == "data_engineering"
