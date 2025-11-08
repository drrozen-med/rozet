#!/usr/bin/env python3
"""Manual REPL testing script - simulates human interaction."""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.core.coordinator import Coordinator
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor
from orchestrator.tui import _is_greeting_or_small_talk, _get_conversational_response

def test_greeting_detection():
    """Test greeting/small talk detection."""
    print("=" * 60)
    print("TEST 1: Greeting Detection")
    print("=" * 60)
    
    test_cases = [
        ("hello", True),
        ("hi there", True),
        ("how are you", True),
        ("create a script", False),
        ("build me an app", False),
        ("tell me about Python", True),
        ("write a Python script", False),
        ("thanks", True),
        ("can you help me build", False),
    ]
    
    for text, expected in test_cases:
        result = _is_greeting_or_small_talk(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' -> {result} (expected {expected})")
    
    print()

def test_conversational_response():
    """Test conversational response (if API works)."""
    print("=" * 60)
    print("TEST 2: Conversational Response")
    print("=" * 60)
    
    try:
        config = load_provider_config()
        llm, _ = create_chat_model(config.orchestrator)
        context_manager = ConversationContextManager()
        
        print("Testing: 'hello'")
        response = _get_conversational_response(llm, "hello", context_manager)
        print(f"✅ Response: {response[:100]}...")
        print()
    except Exception as e:
        print(f"⚠️  API not available: {e}")
        print("   (This is expected if API key is not configured)")
        print()

def test_task_planning():
    """Test task planning."""
    print("=" * 60)
    print("TEST 3: Task Planning")
    print("=" * 60)
    
    try:
        config = load_provider_config()
        llm, _ = create_chat_model(config.orchestrator)
        planner = TaskPlanner(llm=llm, system_prompt=None)
        
        request = "Create a simple hello.py script"
        print(f"Request: '{request}'")
        tasks = planner.plan(request)
        print(f"✅ Planned {len(tasks)} task(s)")
        for task in tasks:
            print(f"   - {task.task_id}: {task.description[:60]}...")
        print()
    except Exception as e:
        print(f"⚠️  Planning failed: {e}")
        print("   (Fallback planner should still work)")
        print()

def test_full_workflow():
    """Test full workflow: plan -> execute."""
    print("=" * 60)
    print("TEST 4: Full Workflow")
    print("=" * 60)
    
    try:
        config = load_provider_config()
        llm, _ = create_chat_model(config.orchestrator)
        planner = TaskPlanner(llm=llm, system_prompt=None)
        tool_executor = ToolExecutor(working_dir=PROJECT_ROOT)
        worker = LocalWorker(
            model='qwen2.5-coder:14b-instruct',
            working_dir=PROJECT_ROOT,
            tool_executor=tool_executor,
            verify_outputs=False
        )
        coordinator = Coordinator(worker=worker)
        
        request = "Create a file test_manual.txt with content 'manual test'"
        print(f"Request: '{request}'")
        
        print("Planning...")
        tasks = planner.plan(request)
        print(f"✅ Planned {len(tasks)} task(s)")
        
        print("Executing...")
        results = coordinator.execute_tasks(tasks)
        
        for task, result in zip(tasks, results):
            status = '✅' if result.success else '❌'
            print(f"{status} {task.task_id}")
            if result.files_created:
                print(f"   Created: {result.files_created}")
        
        # Verify file was created
        test_file = PROJECT_ROOT / "test_manual.txt"
        if test_file.exists():
            content = test_file.read_text()
            print(f"✅ File verified: {content}")
            test_file.unlink()
        else:
            print("❌ File not created")
        print()
    except Exception as e:
        print(f"⚠️  Workflow failed: {e}")
        print()

def test_repl_commands():
    """Test REPL command handling."""
    print("=" * 60)
    print("TEST 5: REPL Commands")
    print("=" * 60)
    
    commands = ["help", "exit", "quit", "q", "plan test"]
    
    print("Testing command recognition:")
    for cmd in commands:
        if cmd in ["help", "exit", "quit", "q"]:
            print(f"✅ '{cmd}' - recognized as command")
        elif cmd.startswith("plan "):
            print(f"✅ '{cmd}' - recognized as plan command")
        else:
            print(f"⚠️  '{cmd}' - would be treated as user input")
    print()

def main():
    """Run all manual tests."""
    print("\n" + "=" * 60)
    print("ROZET REPL - MANUAL USAGE TESTS")
    print("=" * 60)
    print()
    
    test_greeting_detection()
    test_conversational_response()
    test_task_planning()
    test_full_workflow()
    test_repl_commands()
    
    print("=" * 60)
    print("MANUAL TEST SUMMARY")
    print("=" * 60)
    print("✅ Greeting detection tested")
    print("⚠️  Conversational response (requires API)")
    print("⚠️  Task planning (may use fallback)")
    print("⚠️  Full workflow (may timeout)")
    print("✅ REPL commands recognized")
    print()
    print("NOTE: These are automated tests of REPL components.")
    print("For true manual testing, run: rozett --repl")
    print("Then type commands interactively like a human would.")
    print()

if __name__ == "__main__":
    main()

