"""Task planning utilities for decomposing user requests."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

LOGGER = logging.getLogger(__name__)
DEFAULT_SYSTEM_PROMPT = """
You are a senior software architect who coordinates multiple coding agents.
Break the user's request into atomic tasks. For each task provide:
- description: short imperative sentence
- files: list of files to read/write (empty list allowed)
- success_criteria: bullet-style list of verifiable checks
- budget: estimated token/effort budget (small, medium, large)
- dependencies: optional list of task_ids this task depends on
Return JSON with the schema:
{
  "tasks": [
     {
       "task_id": "T1",
       "description": "...",
       "files": ["path/to/file"],
       "success_criteria": ["..."],
       "budget": "medium",
       "dependencies": ["T0"]
     }
  ]
}
Keep tasks between 1 and 6 items. Respond with JSON only.
""".strip()


@dataclass
class TaskSpec:
    task_id: str
    description: str
    files: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    budget: str = "medium"
    dependencies: List[str] = field(default_factory=list)


class TaskPlanner:
    """Uses an LLM to translate requests into structured tasks."""

    def __init__(
        self,
        llm: BaseChatModel,
        *,
        system_prompt: Optional[str] = None,
        max_tasks: int = 6,
    ) -> None:
        self._llm = llm
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._max_tasks = max_tasks

    def plan(self, request: str, context_summary: str = "") -> List[TaskSpec]:
        prompt = self._build_prompt(request, context_summary)
        response = self._llm.invoke(prompt)
        raw_text = getattr(response, "content", str(response))
        LOGGER.debug("Planner raw response: %s", raw_text)
        
        # Extract JSON from markdown code blocks if present
        if "```json" in raw_text:
            start = raw_text.find("```json") + 7
            end = raw_text.find("```", start)
            raw_text = raw_text[start:end].strip()
        elif "```" in raw_text:
            start = raw_text.find("```") + 3
            end = raw_text.find("```", start)
            raw_text = raw_text[start:end].strip()
        
        # Remove any leading/trailing whitespace
        raw_text = raw_text.strip()
        
        if not raw_text:
            LOGGER.error("Planner returned empty response")
            raise ValueError("Planner returned empty response")
        
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            LOGGER.error("Planner returned invalid JSON: %s", exc)
            LOGGER.error("Raw response was: %s", raw_text[:500])
            raise
        tasks_payload = payload.get("tasks", [])[: self._max_tasks]
        tasks: List[TaskSpec] = []
        for entry in tasks_payload:
            try:
                task = TaskSpec(
                    task_id=str(entry.get("task_id") or f"T{len(tasks)+1}"),
                    description=str(entry.get("description", "")).strip(),
                    files=[str(f) for f in entry.get("files", [])],
                    success_criteria=[str(c).strip() for c in entry.get("success_criteria", [])],
                    budget=str(entry.get("budget", "medium")),
                    dependencies=[str(d) for d in entry.get("dependencies", [])],
                )
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.error("Failed to parse task entry %s: %s", entry, exc)
                continue
            tasks.append(task)
        return tasks

    def _build_prompt(self, request: str, context_summary: str) -> List[SystemMessage]:
        messages: List[SystemMessage] = [SystemMessage(content=self._system_prompt)]
        user_instructions = {
            "user_request": request,
            "context_summary": context_summary,
            "max_tasks": self._max_tasks,
        }
        messages.append(HumanMessage(content=json.dumps(user_instructions)))
        return messages
