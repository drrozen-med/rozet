"""Integration tests for OpenCode provider bridge."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.config_loader import ProviderConfig, ProviderMap
from orchestrator.integrations.opencode_provider_bridge import OpenCodeProviderBridge


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
        workers={},
        credentials={"openai": "OPENAI_API_KEY"},
        budget={},
    )


@pytest.fixture
def bridge_without_opencode(mock_config, tmp_path: Path):
    """Create bridge without OpenCode SDK (standalone mode)."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            return bridge


def test_list_providers_standalone(bridge_without_opencode):
    """Test listing providers in standalone mode (no OpenCode SDK)."""
    providers = bridge_without_opencode.list_providers()
    assert "openai" in providers
    assert len(providers) >= 1


def test_list_models_standalone(bridge_without_opencode):
    """Test listing models in standalone mode."""
    models = bridge_without_opencode.list_models("openai")
    assert "gpt-5-nano" in models


def test_get_default_model(bridge_without_opencode):
    """Test getting default model from our config (not OpenCode's hardcoded)."""
    provider_id, model_id = bridge_without_opencode.get_default_model()
    assert provider_id == "openai"
    assert model_id == "gpt-5-nano"


def test_get_current_model(bridge_without_opencode):
    """Test getting current model."""
    provider_id, model_id = bridge_without_opencode.get_current_model()
    assert provider_id == "openai"
    assert model_id == "gpt-5-nano"


def test_validate_model_valid(bridge_without_opencode):
    """Test validating a valid model."""
    assert bridge_without_opencode.validate_model("openai", "gpt-5-nano") is True


def test_validate_model_invalid(bridge_without_opencode):
    """Test validating an invalid model."""
    assert bridge_without_opencode.validate_model("openai", "invalid-model") is False
    assert bridge_without_opencode.validate_model("invalid-provider", "gpt-5-nano") is False


def test_switch_model_success(bridge_without_opencode):
    """Test switching to a valid model."""
    # First add the model to workers so it's valid
    bridge_without_opencode.config.workers["test"] = ProviderConfig(
        provider="anthropic",
        model="claude-3-5-sonnet",
        temperature=0.0,
    )
    
    result = bridge_without_opencode.switch_model("anthropic", "claude-3-5-sonnet")
    assert result is True
    
    # Verify switch
    provider_id, model_id = bridge_without_opencode.get_current_model()
    assert provider_id == "anthropic"
    assert model_id == "claude-3-5-sonnet"


def test_switch_model_invalid(bridge_without_opencode):
    """Test switching to an invalid model (should fail)."""
    result = bridge_without_opencode.switch_model("openai", "invalid-model")
    assert result is False
    
    # Verify original model unchanged
    provider_id, model_id = bridge_without_opencode.get_current_model()
    assert provider_id == "openai"
    assert model_id == "gpt-5-nano"


def test_get_model_info_standalone(bridge_without_opencode):
    """Test getting model info in standalone mode."""
    info = bridge_without_opencode.get_model_info("openai", "gpt-5-nano")
    assert info is not None
    assert info["provider_id"] == "openai"
    assert info["model_id"] == "gpt-5-nano"
    assert info["source"] == "config"


def test_get_model_info_invalid(bridge_without_opencode):
    """Test getting info for invalid model."""
    info = bridge_without_opencode.get_model_info("openai", "invalid-model")
    assert info is None


@pytest.fixture
def mock_opencode_client():
    """Create a mock OpenCode client."""
    client = MagicMock()
    
    # Mock provider response
    provider = MagicMock()
    provider.id = "openai"
    provider.models = {
        "gpt-5-nano": MagicMock(name="gpt-5-nano"),
        "gpt-4": MagicMock(name="gpt-4"),
    }
    
    response = MagicMock()
    response.providers = [provider]
    response.default = {"provider_id": "openai", "model_id": "gpt-5-nano"}
    
    client.config_providers.return_value = response
    return client


def test_list_providers_with_opencode(mock_config, tmp_path: Path, mock_opencode_client):
    """Test listing providers with OpenCode SDK."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", True):
        with patch("orchestrator.integrations.opencode_provider_bridge.OpenCodeClient", return_value=mock_opencode_client):
            with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config):
                bridge = OpenCodeProviderBridge(working_dir=tmp_path)
                providers = bridge.list_providers()
                assert "openai" in providers


def test_list_models_with_opencode(mock_config, tmp_path: Path, mock_opencode_client):
    """Test listing models with OpenCode SDK."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", True):
        with patch("orchestrator.integrations.opencode_provider_bridge.OpenCodeClient", return_value=mock_opencode_client):
            with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config):
                bridge = OpenCodeProviderBridge(working_dir=tmp_path)
                models = bridge.list_models("openai")
                assert "gpt-5-nano" in models
                assert "gpt-4" in models

