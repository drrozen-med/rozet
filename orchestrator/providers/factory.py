"""Factory functions for creating chat models from provider configuration."""

from __future__ import annotations

import importlib
import logging
from typing import Optional, Tuple

from langchain_core.language_models.chat_models import BaseChatModel

from ..config_loader import ProviderConfig

LOGGER = logging.getLogger(__name__)


def create_chat_model(config: ProviderConfig) -> Tuple[BaseChatModel, Optional[str]]:
    """Instantiate a LangChain chat model based on provider configuration."""

    provider = config.provider.lower()
    if provider == "openai":
        model = _build_openai_model(config)
    elif provider == "gemini":
        model = _build_gemini_model(config)
    elif provider == "anthropic":
        model = _build_anthropic_model(config)
    elif provider == "ollama":
        model = _build_ollama_model(config)
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")

    prompt = config.system_prompt()
    LOGGER.info(
        "Loaded chat model provider=%s model=%s temperature=%s",
        config.provider,
        config.model,
        config.temperature,
    )
    return model, prompt


def _build_openai_model(config: ProviderConfig) -> BaseChatModel:
    import os
    module = importlib.import_module("langchain_openai")
    ChatOpenAI = getattr(module, "ChatOpenAI")
    
    # Check if using OpenRouter (custom endpoint)
    is_openrouter = config.endpoint and "openrouter.ai" in config.endpoint.lower()
    
    # Get API key from environment
    # OpenRouter uses OPENROUTER_API_KEY, OpenAI uses OPENAI_API_KEY
    if is_openrouter:
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable not set. "
                "When using OpenRouter, set: export OPENROUTER_API_KEY='your-openrouter-key'"
            )
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it: export OPENAI_API_KEY='your-key-here'"
            )
    
    return ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        base_url=config.endpoint,
        api_key=api_key,
    )


def _build_gemini_model(config: ProviderConfig) -> BaseChatModel:
    import os
    module = importlib.import_module("langchain_google_genai")
    ChatGoogleGenerativeAI = getattr(module, "ChatGoogleGenerativeAI")
    
    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable not set. "
            "Please set it: export GEMINI_API_KEY='your-key-here'"
        )
    
    return ChatGoogleGenerativeAI(
        model=config.model,
        temperature=config.temperature,
        google_api_key=api_key,
    )


def _build_anthropic_model(config: ProviderConfig) -> BaseChatModel:
    import os
    module = importlib.import_module("langchain_anthropic")
    ChatAnthropic = getattr(module, "ChatAnthropic")
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Please set it: export ANTHROPIC_API_KEY='your-key-here'"
        )
    
    return ChatAnthropic(
        model=config.model,
        temperature=config.temperature,
        api_key=api_key,
    )


def _build_ollama_model(config: ProviderConfig) -> BaseChatModel:
    """Build an Ollama chat model for local inference."""
    module = importlib.import_module("langchain_ollama")
    ChatOllama = getattr(module, "ChatOllama")
    # Extract base URL if provided, otherwise use default localhost
    base_url = config.endpoint or "http://localhost:11434"
    return ChatOllama(
        model=config.model,
        temperature=config.temperature,
        base_url=base_url,
    )
