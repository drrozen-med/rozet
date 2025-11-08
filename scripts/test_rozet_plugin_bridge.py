#!/usr/bin/env python3
"""Multi-turn test for Rozet OpenCode plugin bridge."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BRIDGE = PROJECT_ROOT / "orchestrator" / "integrations" / "opencode_plugin_bridge.py"

MESSAGES = [
    "hello",
    "what can you do?",
    "create a file demo.txt with hello world",
    "add tests for the new file",
    "thanks"
]

def run_bridge(message: str) -> dict:
    env = os.environ.copy()
    env.setdefault("ROZET_AUTO_EXECUTE", "1")
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    result = subprocess.run(
        ["python3", str(BRIDGE), "--message", message, "--directory", str(PROJECT_ROOT)],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"⚠️  Bridge returned error for '{message}': {result.stderr.strip() or result.stdout.strip()}")
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON output for '{message}': {result.stdout!r}")
        return {"error": "invalid_json", "raw": result.stdout}


def main() -> None:
    print("Rozet Plugin Bridge Multi-Turn Test\n")
    for idx, message in enumerate(MESSAGES, 1):
        print(f"=== Turn {idx} ===")
        print(f"User: {message}")
        response = run_bridge(message)
        if "error" in response:
            print(f"  ⚠️ Error: {response['error']}")
        else:
            tasks = response.get("tasks", [])
            print(f"  Tasks planned: {len(tasks)}")
            for task in tasks:
                print(f"    - {task['task_id']}: {task['description']}")
            system_prompt = "present" if response.get("systemPrompt") else "none"
            print(f"  System prompt: {system_prompt}")
            print(f"  Needs execution: {response.get('needsExecution')}")
        print()

if __name__ == "__main__":
    main()
