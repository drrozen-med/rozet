"""Integration tests for OpenCode model filtering (blacklist/whitelist)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.config_loader import OpenCodeConfig, ProviderConfig, ProviderMap
from orchestrator.integrations.opencode_provider_bridge import OpenCodeProviderBridge


@pytest.fixture
def mock_config_with_filtering(tmp_path: Path) -> ProviderMap:
    """Create a mock provider config with filtering enabled."""
    return ProviderMap(
        orchestrator=ProviderConfig(
            provider="openai",
            model="gpt-5-nano",
            temperature=0.0,
        ),
        workers={
            "local": ProviderConfig(
                provider="ollama",
                model="qwen2.5-coder:14b",
                temperature=0.0,
            ),
        },
        credentials={},
        budget={},
        opencode=OpenCodeConfig(
            disabled_models=["gpt-5-chat-latest", "invalid-model"],
            allowed_models_only=False,
            allowed_models=[],
            provider_priority=["openai", "ollama"],
        ),
    )


def test_model_blacklist_filtering(mock_config_with_filtering, tmp_path: Path):
    """Test that disabled models are filtered out."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config_with_filtering):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Mock list_models to return models including blacklisted one
            original_list = bridge.list_models
            
            def mock_list(provider_id: str):
                if provider_id == "openai":
                    # Return models including blacklisted
                    return ["gpt-5-nano", "gpt-5-chat-latest", "gpt-4"]
                return original_list(provider_id)
            
            # Apply filter manually to test
            models = ["gpt-5-nano", "gpt-5-chat-latest", "gpt-4"]
            filtered = bridge._apply_model_filters(models, "openai")
            
            # Blacklisted model should be removed
            assert "gpt-5-chat-latest" not in filtered
            assert "gpt-5-nano" in filtered
            assert "gpt-4" in filtered


def test_model_whitelist_filtering(tmp_path: Path):
    """Test that whitelist mode only shows allowed models."""
    config = ProviderMap(
        orchestrator=ProviderConfig(
            provider="openai",
            model="gpt-5-nano",
            temperature=0.0,
        ),
        workers={},
        credentials={},
        budget={},
        opencode=OpenCodeConfig(
            disabled_models=[],
            allowed_models_only=True,
            allowed_models=["openai/gpt-5-nano", "openai/gpt-4"],
            provider_priority=[],
        ),
    )
    
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test whitelist filtering
            models = ["gpt-5-nano", "gpt-4", "gpt-3.5-turbo", "gpt-5-chat-latest"]
            filtered = bridge._apply_model_filters(models, "openai")
            
            # Only whitelisted models should remain
            assert "gpt-5-nano" in filtered
            assert "gpt-4" in filtered
            assert "gpt-3.5-turbo" not in filtered
            assert "gpt-5-chat-latest" not in filtered


def test_model_filtering_combined(tmp_path: Path):
    """Test combining blacklist and whitelist."""
    config = ProviderMap(
        orchestrator=ProviderConfig(
            provider="openai",
            model="gpt-5-nano",
            temperature=0.0,
        ),
        workers={},
        credentials={},
        budget={},
        opencode=OpenCodeConfig(
            disabled_models=["gpt-5-chat-latest"],
            allowed_models_only=True,
            allowed_models=["openai/gpt-5-nano", "openai/gpt-4", "openai/gpt-5-chat-latest"],
            provider_priority=[],
        ),
    )
    
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test combined filtering (blacklist applied first, then whitelist)
            models = ["gpt-5-nano", "gpt-4", "gpt-5-chat-latest", "gpt-3.5-turbo"]
            filtered = bridge._apply_model_filters(models, "openai")
            
            # Blacklist removes gpt-5-chat-latest first
            # Then whitelist only allows gpt-5-nano and gpt-4
            assert "gpt-5-nano" in filtered
            assert "gpt-4" in filtered
            assert "gpt-5-chat-latest" not in filtered  # Blacklisted
            assert "gpt-3.5-turbo" not in filtered  # Not whitelisted


def test_model_filtering_no_filters(tmp_path: Path):
    """Test that models pass through when no filters are configured."""
    config = ProviderMap(
        orchestrator=ProviderConfig(
            provider="openai",
            model="gpt-5-nano",
            temperature=0.0,
        ),
        workers={},
        credentials={},
        budget={},
        opencode=OpenCodeConfig(
            disabled_models=[],
            allowed_models_only=False,
            allowed_models=[],
            provider_priority=[],
        ),
    )
    
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test no filtering
            models = ["gpt-5-nano", "gpt-4", "gpt-3.5-turbo"]
            filtered = bridge._apply_model_filters(models, "openai")
            
            # All models should pass through
            assert len(filtered) == len(models)
            assert all(m in filtered for m in models)

