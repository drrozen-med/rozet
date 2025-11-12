"""Integration tests for OpenCode provider API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config_loader import ProviderConfig, ProviderMap
from orchestrator.integrations.opencode_provider_api import OpenCodeProviderAPI


@pytest.fixture
def mock_config(tmp_path: Path) -> ProviderMap:
    """Create a mock provider config."""
    return ProviderMap(
        orchestrator=ProviderConfig(
            provider="openai",
            model="gpt-5-nano",
            temperature=0.0,
            endpoint="https://openrouter.ai/api/v1",
        ),
        workers={
            "local": ProviderConfig(
                provider="ollama",
                model="qwen2.5-coder:14b",
                temperature=0.0,
            ),
        },
        credentials={"openai": "OPENAI_API_KEY"},
        budget={},
    )


@pytest.fixture
def api_without_opencode(mock_config, tmp_path: Path):
    """Create API without OpenCode SDK (standalone mode)."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config):
            api = OpenCodeProviderAPI(working_dir=tmp_path)
            return api


def test_get_current_model(api_without_opencode):
    """Test getting current model."""
    provider, model = api_without_opencode.get_current_model()
    assert provider == "openai"
    assert model == "gpt-5-nano"


def test_list_providers(api_without_opencode):
    """Test listing providers."""
    providers = api_without_opencode.list_providers()
    assert "openai" in providers
    assert "ollama" in providers


def test_list_available_models_all(api_without_opencode):
    """Test listing all available models."""
    models = api_without_opencode.list_available_models()
    assert len(models) >= 2  # At least openai and ollama models
    
    # Check structure
    for model in models:
        assert "provider_id" in model
        assert "model_id" in model


def test_list_available_models_filtered(api_without_opencode):
    """Test listing models for specific provider."""
    models = api_without_opencode.list_available_models("openai")
    assert len(models) >= 1
    assert all(m["provider_id"] == "openai" for m in models)


def test_validate_model_valid(api_without_opencode):
    """Test validating a valid model."""
    assert api_without_opencode.validate_model("openai", "gpt-5-nano") is True
    assert api_without_opencode.validate_model("ollama", "qwen2.5-coder:14b") is True


def test_validate_model_invalid(api_without_opencode):
    """Test validating an invalid model."""
    assert api_without_opencode.validate_model("openai", "invalid-model") is False
    assert api_without_opencode.validate_model("invalid-provider", "gpt-5-nano") is False


def test_switch_model_success(api_without_opencode):
    """Test switching to a valid model."""
    # Switch to ollama model (exists in workers)
    result = api_without_opencode.switch_model("ollama", "qwen2.5-coder:14b")
    assert result is True
    
    # Verify switch
    provider, model = api_without_opencode.get_current_model()
    assert provider == "ollama"
    assert model == "qwen2.5-coder:14b"


def test_switch_model_invalid(api_without_opencode):
    """Test switching to an invalid model (should fail)."""
    result = api_without_opencode.switch_model("openai", "invalid-model")
    assert result is False
    
    # Verify original model unchanged
    provider, model = api_without_opencode.get_current_model()
    assert provider == "openai"
    assert model == "gpt-5-nano"


def test_get_model_info(api_without_opencode):
    """Test getting model info."""
    info = api_without_opencode.get_model_info("openai", "gpt-5-nano")
    assert info is not None
    assert info["provider_id"] == "openai"
    assert info["model_id"] == "gpt-5-nano"


def test_get_default_model(api_without_opencode):
    """Test getting default model (from our config, not hardcoded)."""
    provider, model = api_without_opencode.get_default_model()
    assert provider == "openai"
    assert model == "gpt-5-nano"


def test_get_default_model_after_switch(api_without_opencode):
    """Test that get_default_model returns config default, not current."""
    # Switch model
    api_without_opencode.switch_model("ollama", "qwen2.5-coder:14b")
    
    # get_default_model should still return config default
    provider, model = api_without_opencode.get_default_model()
    assert provider == "openai"
    assert model == "gpt-5-nano"
    
    # But get_current_model should return switched model
    provider, model = api_without_opencode.get_current_model()
    assert provider == "ollama"
    assert model == "qwen2.5-coder:14b"

