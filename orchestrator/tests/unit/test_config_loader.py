"""Unit tests for config loader (no API calls)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from orchestrator.config_loader import ConfigurationError, load_provider_config


def test_load_valid_config():
    """Test loading a valid config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "orchestrator": {
                "provider": "openai",
                "model": "gpt-5-nano",
                "temperature": 0.0,
            },
            "credentials": {
                "openai": "OPENAI_API_KEY",
            },
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        # Disable strict credential validation for testing
        import os
        os.environ["ORCHESTRATOR_STRICT_CREDENTIALS"] = "false"
        
        config = load_provider_config(config_path)
        
        assert config.orchestrator.provider == "openai"
        assert config.orchestrator.model == "gpt-5-nano"
        assert config.orchestrator.temperature == 0.0
    finally:
        config_path.unlink()


def test_load_missing_orchestrator():
    """Test that missing orchestrator section raises error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "credentials": {
                "openai": "OPENAI_API_KEY",
            },
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ConfigurationError, match="orchestrator"):
            load_provider_config(config_path)
    finally:
        config_path.unlink()


def test_system_prompt_path():
    """Test system prompt path resolution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config file
        config_file = Path(tmpdir) / "config.yaml"
        prompt_file = Path(tmpdir) / "prompt.md"
        prompt_file.write_text("# Test prompt")
        
        config_data = {
            "orchestrator": {
                "provider": "openai",
                "model": "gpt-5-nano",
                "system_prompt_path": str(prompt_file),  # Use absolute path
            },
            "credentials": {
                "openai": "OPENAI_API_KEY",
            },
        }
        with config_file.open("w") as f:
            yaml.dump(config_data, f)
        
        # Disable strict credential validation
        import os
        os.environ["ORCHESTRATOR_STRICT_CREDENTIALS"] = "false"
        
        config = load_provider_config(config_file)
        
        # System prompt should be loaded
        prompt = config.orchestrator.system_prompt()
        assert prompt is not None
        assert "# Test prompt" in prompt

