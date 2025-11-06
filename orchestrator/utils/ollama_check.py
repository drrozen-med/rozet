"""Utility functions for checking Ollama availability."""

from __future__ import annotations

import logging
import subprocess

LOGGER = logging.getLogger(__name__)


def check_ollama_available() -> bool:
    """Check if Ollama is available and running.
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        # Try to run ollama list command
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as exc:
        LOGGER.debug("Ollama not available: %s", exc)
        return False


def check_ollama_model_available(model_name: str) -> bool:
    """Check if a specific Ollama model is available.
    
    Args:
        model_name: Name of the model to check (e.g., "qwen2.5-coder:14b-instruct")
        
    Returns:
        True if model is available, False otherwise
    """
    if not check_ollama_available():
        return False
    
    try:
        # Try to list models and check if our model is in the list
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            return False
        
        # Check if model name appears in output
        # Model names can be "model:tag" format
        output = result.stdout.lower()
        model_lower = model_name.lower()
        
        # Check for exact match or prefix match (for tags)
        return model_lower in output or any(
            line.startswith(model_lower.split(":")[0]) for line in output.split("\n")
        )
    except Exception as exc:
        LOGGER.debug("Failed to check Ollama model %s: %s", model_name, exc)
        return False

