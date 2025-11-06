"""Tests for environment overrides in config loader."""

from __future__ import annotations

import textwrap

import pytest

from orchestrator.config_loader import load_provider_config


def test_orchestrator_env_overrides(tmp_path, monkeypatch):
    config_yaml = tmp_path / "providers.yaml"
    config_yaml.write_text(
        textwrap.dedent(
            """
            orchestrator:
              provider: openai
              model: gpt-5-nano
              temperature: 0.1
              endpoint: https://openrouter.ai/api/v1
              system_prompt_path: prompts/orchestrator.md
            """
        )
    )

    monkeypatch.setenv("ROZET_ORCHESTRATOR_PROVIDER", "ollama")
    monkeypatch.setenv("ROZET_ORCHESTRATOR_MODEL", "gpt-oss:20b")
    monkeypatch.setenv("ROZET_ORCHESTRATOR_ENDPOINT", "http://localhost:11434")
    monkeypatch.setenv("ROZET_ORCHESTRATOR_TEMPERATURE", "0.0")
    monkeypatch.setenv("ROZET_ORCHESTRATOR_SYSTEM_PROMPT", "prompts/local.md")
    monkeypatch.setenv("ORCHESTRATOR_STRICT_CREDENTIALS", "false")

    config = load_provider_config(config_yaml)

    orch = config.orchestrator
    assert orch.provider == "ollama"
    assert orch.model == "gpt-oss:20b"
    assert orch.endpoint == "http://localhost:11434"
    assert orch.temperature == 0.0
    assert orch.system_prompt_path == "prompts/local.md"

