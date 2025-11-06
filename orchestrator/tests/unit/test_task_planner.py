"""Tests for TaskPlanner fallback logic."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from orchestrator.core.task_planner import TaskPlanner, TaskSpec


@dataclass
class FakeResponse:
    content: str


class FailingLLM:
    def __init__(self, error: Exception):
        self.error = error

    def invoke(self, _prompt):
        raise self.error


class InvalidJSONLLM:
    def invoke(self, _prompt):
        return FakeResponse("not-json")


def test_task_planner_fallback_on_error():
    planner = TaskPlanner(llm=FailingLLM(RuntimeError("boom")))
    tasks = planner.plan("write a script")
    assert len(tasks) == 1
    assert isinstance(tasks[0], TaskSpec)
    assert "write a script" in tasks[0].description.lower()


def test_task_planner_fallback_on_invalid_json():
    planner = TaskPlanner(llm=InvalidJSONLLM())
    tasks = planner.plan("add readme")
    assert len(tasks) == 1
    assert "add readme" in tasks[0].description.lower()

