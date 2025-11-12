"""OpenCode provider bridge - clean API for model/provider operations.

This module provides a clean, config-driven interface to OpenCode's provider/model
system, replacing OpenCode's hardcoded priorities and complex state management
with our simple, testable approach.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Try to import OpenCode SDK (optional - bridge works without it)
try:
    # Add OpenCode SDK to path if available
    opencode_sdk_path = Path(__file__).parent.parent.parent / "opencode" / "packages" / "sdk" / "python" / "src"
    if opencode_sdk_path.exists():
        sys.path.insert(0, str(opencode_sdk_path))
    from opencode_ai import OpenCodeClient
    from opencode_ai.models.provider import Provider
    OPencode_AVAILABLE = True
except ImportError:
    OPencode_AVAILABLE = False
    OpenCodeClient = None  # type: ignore
    Provider = None  # type: ignore

from orchestrator.config_loader import OpenCodeConfig, ProviderMap, load_provider_config

LOGGER = logging.getLogger(__name__)


class OpenCodeProviderBridge:
    """Bridge between OpenCode's provider system and our clean interface.
    
    This class:
    - Uses our config as source of truth
    - Provides clean API for model/provider operations
    - Overrides OpenCode's hardcoded priorities
    - Makes model switching programmatically controllable
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        opencode_base_url: str = "http://localhost:4096",
        working_dir: Optional[Path] = None,
    ):
        """Initialize the provider bridge.
        
        Args:
            config_path: Path to provider config YAML (defaults to config/providers.yaml)
            opencode_base_url: Base URL for OpenCode server
            working_dir: Working directory (for OpenCode project detection)
        """
        self.working_dir = working_dir or Path.cwd()
        self.config_path = config_path
        self.opencode_base_url = opencode_base_url
        
        # Load our orchestrator configuration (source of truth)
        self.config = load_provider_config(config_path)
        
        # Store original config for get_default_model (always returns original, not switched)
        self._original_config = (self.config.orchestrator.provider, self.config.orchestrator.model)
        
        # Initialize OpenCode client if available
        if OPencode_AVAILABLE and OpenCodeClient:
            try:
                self.opencode_client = OpenCodeClient(base_url=opencode_base_url)
                LOGGER.info("OpenCode client initialized at %s", opencode_base_url)
            except Exception as e:
                LOGGER.warning("Failed to initialize OpenCode client: %s", e)
                self.opencode_client = None
        else:
            self.opencode_client = None
            LOGGER.info("OpenCode SDK not available - bridge will work in standalone mode")
        
        # Cache for provider/model data
        self._providers_cache: Optional[Dict[str, Provider]] = None
        self._default_model_cache: Optional[Tuple[str, str]] = None
    
    def list_providers(self) -> List[str]:
        """List available providers (ordered by provider_priority from config).
        
        Returns:
            List of provider IDs, ordered by provider_priority if configured
        """
        if not self.opencode_client:
            # Fallback to our config
            providers = [self.config.orchestrator.provider]
            for worker_config in self.config.workers.values():
                if worker_config.provider not in providers:
                    providers.append(worker_config.provider)
            return self._apply_provider_priority(providers)
        
        try:
            response = self.opencode_client.config_providers(directory=str(self.working_dir))
            if response and response.providers:
                providers = [p.id for p in response.providers if p.id]
                return self._apply_provider_priority(providers)
            return []
        except Exception as e:
            LOGGER.warning("Failed to list providers from OpenCode: %s", e)
            # Fallback to our config
            providers = [self.config.orchestrator.provider]
            return self._apply_provider_priority(providers)
    
    def list_models(self, provider_id: str) -> List[str]:
        """List available models for a provider (with filtering applied).
        
        Args:
            provider_id: Provider ID (e.g., 'openai', 'anthropic')
            
        Returns:
            List of model IDs for the provider (filtered by our config)
        """
        if not self.opencode_client:
            # Fallback: check our config (orchestrator + workers)
            models = []
            if provider_id.lower() == self.config.orchestrator.provider.lower():
                models.append(self.config.orchestrator.model)
            # Also check workers
            for worker_config in self.config.workers.values():
                if provider_id.lower() == worker_config.provider.lower():
                    if worker_config.model not in models:
                        models.append(worker_config.model)
            return self._apply_model_filters(models, provider_id)
        
        try:
            response = self.opencode_client.config_providers(directory=str(self.working_dir))
            if not response or not response.providers:
                return []
            
            # Find the provider
            provider = next((p for p in response.providers if p.id == provider_id), None)
            if not provider:
                return []
            
            # Get models from provider
            # Provider has a models attribute (dict-like)
            if hasattr(provider, 'models') and provider.models:
                models = list(provider.models.keys())
                return self._apply_model_filters(models, provider_id)
            
            return []
        except Exception as e:
            LOGGER.warning("Failed to list models for provider %s: %s", provider_id, e)
            # Fallback: if this is our configured provider, return our model
            if provider_id.lower() == self.config.orchestrator.provider.lower():
                models = [self.config.orchestrator.model]
                return self._apply_model_filters(models, provider_id)
            return []
    
    def _apply_model_filters(self, models: List[str], provider_id: str) -> List[str]:
        """Apply model filtering from config (blacklist, whitelist).
        
        Args:
            models: List of model IDs to filter
            provider_id: Provider ID (for full model ID construction)
            
        Returns:
            Filtered list of model IDs
        """
        opencode_config = self.config.opencode
        
        # Apply blacklist (disabled models)
        if opencode_config.disabled_models:
            filtered = []
            for model_id in models:
                full_id = f"{provider_id}/{model_id}"
                # Check both full ID and just model_id
                if full_id not in opencode_config.disabled_models and model_id not in opencode_config.disabled_models:
                    filtered.append(model_id)
            models = filtered
        
        # Apply whitelist (if enabled)
        if opencode_config.allowed_models_only and opencode_config.allowed_models:
            filtered = []
            for model_id in models:
                full_id = f"{provider_id}/{model_id}"
                # Check both full ID and just model_id
                if full_id in opencode_config.allowed_models or model_id in opencode_config.allowed_models:
                    filtered.append(model_id)
            models = filtered
        
        return models
    
    def _apply_provider_priority(self, providers: List[str]) -> List[str]:
        """Apply provider priority ordering from config.
        
        Args:
            providers: List of provider IDs to order
            
        Returns:
            Ordered list of providers (priority first, then rest)
        """
        opencode_config = self.config.opencode
        
        if not opencode_config.provider_priority:
            # No priority configured, return as-is
            return providers
        
        # Separate into priority and non-priority
        priority_providers = []
        rest_providers = []
        
        for provider_id in providers:
            if provider_id in opencode_config.provider_priority:
                # Get index in priority list for sorting
                priority_providers.append((opencode_config.provider_priority.index(provider_id), provider_id))
            else:
                rest_providers.append(provider_id)
        
        # Sort priority providers by their index in priority list
        priority_providers.sort(key=lambda x: x[0])
        priority_sorted = [p[1] for p in priority_providers]
        
        # Return: priority providers first (in order), then rest
        return priority_sorted + rest_providers
    
    def get_default_model(self) -> Tuple[str, str]:
        """Get default provider/model from our config (not OpenCode's hardcoded).
        
        Returns:
            Tuple of (provider_id, model_id)
            
        Note: This always returns the original config default, not the current
        switched model. Use get_current_model() for the active model.
        """
        # Our config is source of truth - no hardcoded priorities!
        # Always return original config, not switched state
        # Store original config at init time
        if not hasattr(self, '_original_config'):
            self._original_config = (self.config.orchestrator.provider, self.config.orchestrator.model)
        return self._original_config
    
    def get_current_model(self) -> Tuple[str, str]:
        """Get current provider/model (from our config, may be switched).
        
        Returns:
            Tuple of (provider_id, model_id)
            
        Note: This returns the current active model (which may have been switched).
        Use get_default_model() to get the original config default.
        """
        # Return current config (which may have been switched)
        return (self.config.orchestrator.provider, self.config.orchestrator.model)
    
    def validate_model(self, provider_id: str, model_id: str) -> bool:
        """Validate that a model is available and configured.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            True if model is available, False otherwise
        """
        # Check our config first (orchestrator + workers)
        if provider_id.lower() == self.config.orchestrator.provider.lower():
            if model_id == self.config.orchestrator.model:
                return True
        
        # Check workers
        for worker_config in self.config.workers.values():
            if provider_id.lower() == worker_config.provider.lower():
                if model_id == worker_config.model:
                    return True
        
        # If OpenCode client available, check there too
        if self.opencode_client:
            try:
                models = self.list_models(provider_id)
                return model_id in models
            except Exception:
                return False
        
        return False
    
    def switch_model(self, provider_id: str, model_id: str) -> bool:
        """Switch to a specific model (updates our config, not OpenCode's state).
        
        Note: This updates our internal config representation. To persist,
        you'd need to write back to config file (future enhancement).
        
        Args:
            provider_id: Provider ID to switch to
            model_id: Model ID to switch to
            
        Returns:
            True if switch was successful, False if model not available
        """
        if not self.validate_model(provider_id, model_id):
            LOGGER.warning("Model %s/%s not available", provider_id, model_id)
            return False
        
        # Update our config (in-memory)
        from dataclasses import replace
        self.config.orchestrator = replace(
            self.config.orchestrator,
            provider=provider_id,
            model=model_id,
        )
        
        LOGGER.info("Switched to model: %s/%s", provider_id, model_id)
        return True
    
    def get_model_info(self, provider_id: str, model_id: str) -> Optional[Dict]:
        """Get information about a specific model.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
            
        Returns:
            Dictionary with model info, or None if not found
        """
        if not self.opencode_client:
            # Fallback: return basic info from our config
            if self.validate_model(provider_id, model_id):
                return {
                    "provider_id": provider_id,
                    "model_id": model_id,
                    "source": "config",
                }
            return None
        
        try:
            response = self.opencode_client.config_providers(directory=str(self.working_dir))
            if not response or not response.providers:
                return None
            
            # Find the provider
            provider = next((p for p in response.providers if p.id == provider_id), None)
            if not provider:
                return None
            
            # Get model info
            if hasattr(provider, 'models') and provider.models:
                model_info = provider.models.get(model_id)
                if model_info:
                    # Convert to dict
                    info = {
                        "provider_id": provider_id,
                        "model_id": model_id,
                        "source": "opencode",
                    }
                    # Add model attributes if available
                    if hasattr(model_info, 'name'):
                        info["name"] = model_info.name
                    if hasattr(model_info, 'cost'):
                        info["cost"] = model_info.cost
                    if hasattr(model_info, 'limit'):
                        info["limit"] = model_info.limit
                    return info
            
            return None
        except Exception as e:
            LOGGER.warning("Failed to get model info for %s/%s: %s", provider_id, model_id, e)
            return None

