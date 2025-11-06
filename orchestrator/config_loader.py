"""Utilities for loading orchestrator configuration files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Load .env file if it exists (before any config loading)
try:
    from dotenv import load_dotenv
    # Try multiple locations (same as entry point)
    project_root = Path(__file__).parent.parent
    env_locations = [
        project_root / ".env",  # Project root
        project_root.parent / ".env",  # Parent directory
        Path.cwd() / ".env",  # Current working directory
        project_root / "credentials" / ".env",  # Credentials directory
    ]
    
    loaded = False
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path, override=not loaded)
            loaded = True
    
    # Also try standard load_dotenv (searches current dir and parents)
    if not loaded:
        load_dotenv(override=False)
except ImportError:
    # python-dotenv not installed, skip
    pass

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_PROVIDER_FILE = CONFIG_DIR / "providers.yaml"
EXAMPLE_PROVIDER_FILE = CONFIG_DIR / "providers.example.yaml"


class ConfigurationError(RuntimeError):
    """Raised when orchestrator configuration cannot be loaded."""


@dataclass
class ProviderConfig:
    """Configuration describing a single provider/model pairing."""

    provider: str
    model: str
    temperature: float = 0.0
    system_prompt_path: Optional[str] = None
    endpoint: Optional[str] = None
    budget_usd: Optional[float] = None
    behavior_profile: Optional[str] = None

    def system_prompt(self) -> Optional[str]:
        if not self.system_prompt_path:
            return None
        prompt_path = Path(self.system_prompt_path)
        if not prompt_path.is_absolute():
            prompt_path = CONFIG_DIR.parent / prompt_path
        if not prompt_path.exists():
            # Return None instead of raising error - allows graceful fallback
            import logging
            logging.getLogger(__name__).warning(
                "System prompt file not found: %s. Using default prompt.", prompt_path
            )
            return None
        return prompt_path.read_text(encoding="utf-8")


@dataclass
class ProviderMap:
    orchestrator: ProviderConfig
    workers: Dict[str, ProviderConfig] = field(default_factory=dict)
    credentials: Dict[str, str] = field(default_factory=dict)
    budget: Dict[str, float] = field(default_factory=dict)


def _normalize_provider(entry: dict) -> ProviderConfig:
    try:
        return ProviderConfig(
            provider=entry["provider"],
            model=entry["model"],
            temperature=float(entry.get("temperature", 0.0)),
            system_prompt_path=entry.get("system_prompt_path"),
            endpoint=entry.get("endpoint"),
            budget_usd=entry.get("budget_usd"),
            behavior_profile=entry.get("behavior_profile"),
        )
    except KeyError as exc:  # pragma: no cover - defensive
        raise ConfigurationError(f"Missing provider field: {exc}") from exc


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigurationError(f"Configuration file missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_provider_config(config_path: Optional[os.PathLike[str]] = None) -> ProviderMap:
    """Load the provider configuration.

    Args:
        config_path: optional override path. Defaults to `config/providers.yaml`.
    """

    resolved_path: Path
    if config_path:
        resolved_path = Path(config_path)
    elif DEFAULT_PROVIDER_FILE.exists():
        resolved_path = DEFAULT_PROVIDER_FILE
    else:
        resolved_path = EXAMPLE_PROVIDER_FILE

    raw = _load_yaml(resolved_path)

    orchestrator_entry = raw.get("orchestrator")
    if not orchestrator_entry:
        raise ConfigurationError("`orchestrator` section missing from provider config")

    workers_entry = raw.get("workers", {})

    workers = {name: _normalize_provider(cfg) for name, cfg in workers_entry.items()}

    config = ProviderMap(
        orchestrator=_normalize_provider(orchestrator_entry),
        workers=workers,
        credentials=raw.get("credentials", {}),
        budget=raw.get("budget", {}),
    )

    # Only validate credentials for providers we're actually using
    strict_validation = os.environ.get("ORCHESTRATOR_STRICT_CREDENTIALS", "true").lower() == "true"
    
    # Determine which providers are actually used
    required_providers = [config.orchestrator.provider.lower()]
    # Also check workers if any are configured
    for worker_config in config.workers.values():
        provider = worker_config.provider.lower()
        if provider not in required_providers:
            required_providers.append(provider)
    
    _validate_credentials(config.credentials, strict=strict_validation, required_providers=required_providers)

    config = _apply_env_overrides(config)
    return config


def _validate_credentials(cred_map: Dict[str, str], strict: bool = True, required_providers: Optional[List[str]] = None) -> None:
    """Validate credentials, optionally allowing missing ones for testing.
    
    Args:
        cred_map: Map of provider -> environment variable name
        strict: If True, raise error on missing credentials
        required_providers: Optional list of providers that must have credentials.
                           If None, validates all providers in cred_map.
    """
    missing: List[str] = []
    providers_to_check = required_providers if required_providers else list(cred_map.keys())
    
    for provider in providers_to_check:
        if provider not in cred_map:
            continue
        env_var = cred_map[provider]
        if env_var and env_var not in os.environ:
            missing.append(f"{provider} (set {env_var})")
    
    if missing:
        joined = ", ".join(missing)
        if strict:
            raise ConfigurationError(
                "Missing provider credentials: "
                f"{joined}. Export the required environment variables or update config."
            )
        else:
            import logging
            logging.getLogger(__name__).warning(
                "Missing provider credentials: %s. Some features may not work.", joined
            )


def _apply_env_overrides(config: ProviderMap) -> ProviderMap:
    """Apply environment variable overrides to provider config."""
    provider_env_prefix = "ROZET_ORCHESTRATOR_"
    overrides = {
        "provider": os.environ.get(f"{provider_env_prefix}PROVIDER"),
        "model": os.environ.get(f"{provider_env_prefix}MODEL"),
        "endpoint": os.environ.get(f"{provider_env_prefix}ENDPOINT"),
        "temperature": os.environ.get(f"{provider_env_prefix}TEMPERATURE"),
        "system_prompt_path": os.environ.get(f"{provider_env_prefix}SYSTEM_PROMPT"),
    }

    # Determine if any overrides are set
    if any(value is not None for value in overrides.values()):
        new_kwargs = {}
        for key, value in overrides.items():
            if value is None:
                continue
            if key == "temperature":
                try:
                    value = float(value)
                except ValueError:
                    continue
            new_kwargs[key] = value
        if new_kwargs:
            config.orchestrator = replace(config.orchestrator, **new_kwargs)

    return config


def dump_provider_config(config: ProviderMap) -> str:
    """Serialize the provider configuration to JSON for debugging/logging."""

    data = {
        "orchestrator": config.orchestrator.__dict__,
        "workers": {name: cfg.__dict__ for name, cfg in config.workers.items()},
        "credentials": config.credentials,
        "budget": config.budget,
    }
    return json.dumps(data, indent=2)
