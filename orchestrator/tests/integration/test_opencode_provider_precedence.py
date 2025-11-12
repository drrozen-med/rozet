"""Integration tests for OpenCode provider precedence/priority."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.config_loader import OpenCodeConfig, ProviderConfig, ProviderMap
from orchestrator.integrations.opencode_provider_bridge import OpenCodeProviderBridge


@pytest.fixture
def mock_config_with_priority(tmp_path: Path) -> ProviderMap:
    """Create a mock provider config with provider priority."""
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
            disabled_models=[],
            allowed_models_only=False,
            allowed_models=[],
            provider_priority=["ollama", "openai", "anthropic"],
        ),
    )


def test_provider_priority_ordering(mock_config_with_priority, tmp_path: Path):
    """Test that providers are ordered by priority."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config_with_priority):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test priority ordering
            providers = ["openai", "anthropic", "ollama", "gemini"]
            ordered = bridge._apply_provider_priority(providers)
            
            # Should be ordered: ollama (first in priority), openai (second), anthropic (third), then gemini
            assert ordered[0] == "ollama"
            assert ordered[1] == "openai"
            assert ordered[2] == "anthropic"
            assert ordered[3] == "gemini"


def test_provider_priority_partial(tmp_path: Path):
    """Test priority when only some providers are in priority list."""
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
            provider_priority=["anthropic", "openai"],
        ),
    )
    
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test with providers not all in priority
            providers = ["openai", "gemini", "anthropic", "ollama"]
            ordered = bridge._apply_provider_priority(providers)
            
            # Priority providers first (anthropic, openai), then rest
            assert ordered[0] == "anthropic"
            assert ordered[1] == "openai"
            # Rest should be after (order not specified)
            assert "gemini" in ordered[2:]
            assert "ollama" in ordered[2:]


def test_provider_priority_empty(tmp_path: Path):
    """Test that no priority means no reordering."""
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
            provider_priority=[],  # Empty priority
        ),
    )
    
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=config):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            # Test with no priority
            providers = ["openai", "anthropic", "ollama"]
            ordered = bridge._apply_provider_priority(providers)
            
            # Should remain in original order (no reordering)
            assert ordered == providers


def test_list_providers_with_priority(mock_config_with_priority, tmp_path: Path):
    """Test that list_providers respects priority."""
    with patch("orchestrator.integrations.opencode_provider_bridge.OPencode_AVAILABLE", False):
        with patch("orchestrator.integrations.opencode_provider_bridge.load_provider_config", return_value=mock_config_with_priority):
            bridge = OpenCodeProviderBridge(working_dir=tmp_path)
            
            providers = bridge.list_providers()
            
            # Should include both providers
            assert "openai" in providers
            assert "ollama" in providers
            
            # ollama should come first (first in priority)
            assert providers[0] == "ollama"

