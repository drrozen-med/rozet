"""Clean programmatic API for OpenCode provider/model operations.

This module provides a simple, testable API for all provider/model operations,
replacing OpenCode's complex, hardcoded system with our config-driven approach.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from orchestrator.integrations.opencode_provider_bridge import OpenCodeProviderBridge

LOGGER = logging.getLogger(__name__)


class OpenCodeProviderAPI:
    """Clean API for OpenCode provider/model operations.
    
    This class provides a simple, programmatic interface for:
    - Switching models
    - Getting current model
    - Listing available models
    - Validating models
    - Getting model metadata
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        opencode_base_url: str = "http://localhost:4096",
        working_dir: Optional[Path] = None,
    ):
        """Initialize the provider API.
        
        Args:
            config_path: Path to provider config YAML
            opencode_base_url: Base URL for OpenCode server
            working_dir: Working directory for OpenCode project
        """
        self._bridge = OpenCodeProviderBridge(
            config_path=config_path,
            opencode_base_url=opencode_base_url,
            working_dir=working_dir,
        )
    
    def switch_model(self, provider_id: str, model_id: str) -> bool:
        """Switch to a specific model.
        
        Args:
            provider_id: Provider ID (e.g., 'openai', 'anthropic')
            model_id: Model ID (e.g., 'gpt-5-nano', 'claude-3-5-sonnet')
            
        Returns:
            True if switch was successful, False if model not available
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> api.switch_model("openai", "gpt-5-nano")
            True
        """
        return self._bridge.switch_model(provider_id, model_id)
    
    def get_current_model(self) -> Tuple[str, str]:
        """Get current provider/model.
        
        Returns:
            Tuple of (provider_id, model_id)
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> provider, model = api.get_current_model()
            >>> print(f"Using {provider}/{model}")
            Using openai/gpt-5-nano
        """
        return self._bridge.get_current_model()
    
    def list_available_models(
        self,
        provider_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """List available models with metadata.
        
        Args:
            provider_id: Optional provider ID to filter by. If None, lists all providers.
            
        Returns:
            List of dictionaries with 'provider_id' and 'model_id' keys
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> models = api.list_available_models("openai")
            >>> for model in models:
            ...     print(f"{model['provider_id']}/{model['model_id']}")
            openai/gpt-5-nano
            openai/gpt-4
        """
        if provider_id:
            model_ids = self._bridge.list_models(provider_id)
            return [
                {"provider_id": provider_id, "model_id": model_id}
                for model_id in model_ids
            ]
        else:
            # List all providers and their models
            providers = self._bridge.list_providers()
            all_models = []
            for prov_id in providers:
                model_ids = self._bridge.list_models(prov_id)
                for model_id in model_ids:
                    all_models.append({
                        "provider_id": prov_id,
                        "model_id": model_id,
                    })
            return all_models
    
    def validate_model(self, provider_id: str, model_id: str) -> bool:
        """Validate that a model is available and configured.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            True if model is available, False otherwise
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> api.validate_model("openai", "gpt-5-nano")
            True
            >>> api.validate_model("openai", "invalid-model")
            False
        """
        return self._bridge.validate_model(provider_id, model_id)
    
    def get_model_info(self, provider_id: str, model_id: str) -> Optional[Dict]:
        """Get detailed information about a model.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            Dictionary with model information, or None if not found
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> info = api.get_model_info("openai", "gpt-5-nano")
            >>> print(info["provider_id"], info["model_id"])
            openai gpt-5-nano
        """
        return self._bridge.get_model_info(provider_id, model_id)
    
    def list_providers(self) -> List[str]:
        """List all available providers.
        
        Returns:
            List of provider IDs
            
        Example:
            >>> api = OpenCodeProviderAPI()
            >>> providers = api.list_providers()
            >>> print(providers)
            ['openai', 'anthropic', 'ollama']
        """
        return self._bridge.list_providers()
    
    def get_default_model(self) -> Tuple[str, str]:
        """Get default model from our config (not OpenCode's hardcoded priorities).
        
        Returns:
            Tuple of (provider_id, model_id)
            
        Note: This uses our config as source of truth, not OpenCode's
        hardcoded priority list.
        """
        return self._bridge.get_default_model()

