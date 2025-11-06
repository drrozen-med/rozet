"""Tests for provider factory (OpenAI/OpenRouter handling)."""

from __future__ import annotations

import importlib
import types

import pytest

from orchestrator.config_loader import ProviderConfig
from orchestrator.providers.factory import create_chat_model


class DummyChatModel:
    """Simple dummy chat model to capture init kwargs."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyModule:
    def __init__(self):
        self.last_kwargs = None

    def ChatOpenAI(self, **kwargs):  # noqa: N802 - mimic class constructor
        self.last_kwargs = kwargs
        return DummyChatModel(**kwargs)


@pytest.fixture()
def fake_chatopenai(monkeypatch):
    module = DummyModule()
    original_import = importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "langchain_openai":
            return module
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    return module


def _make_config(**overrides) -> ProviderConfig:
    base = {
        "provider": "openai",
        "model": "gpt-test",
        "temperature": 0.0,
        "endpoint": None,
        "system_prompt_path": None,
    }
    base.update(overrides)
    return ProviderConfig(**base)


def test_openrouter_headers(monkeypatch, fake_chatopenai):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_HTTP_REFERER", raising=False)
    monkeypatch.delenv("OPENROUTER_X_TITLE", raising=False)

    config = _make_config(endpoint="https://openrouter.ai/api/v1")

    chat_model, _ = create_chat_model(config)

    kwargs = fake_chatopenai.last_kwargs
    assert kwargs is not None
    assert kwargs["api_key"] == "test-key"
    assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
    headers = kwargs.get("default_headers", {})
    assert headers.get("HTTP-Referer") is not None
    assert headers.get("X-Title") is not None


def test_openai_standard(monkeypatch, fake_chatopenai):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    config = _make_config(endpoint=None)

    chat_model, _ = create_chat_model(config)

    kwargs = fake_chatopenai.last_kwargs
    assert kwargs is not None
    assert kwargs["api_key"] == "sk-test"
    assert kwargs["base_url"] is None
    assert "default_headers" not in kwargs or not kwargs["default_headers"]

