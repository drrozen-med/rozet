#!/usr/bin/env python3
"""Simple test runner for Rozet orchestrator components."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor


def test_tool_executor():
    """Test ToolExecutor basic functionality."""
    print("Testing ToolExecutor...")
    try:
        executor = ToolExecutor(working_dir=project_root)
        
        # Test write_file
        test_file = "test_temp_file.txt"
        result = executor.write_file(test_file, "test content")
        if not result["success"]:
            print(f"  ❌ write_file failed: {result}")
            return False
        print("  ✅ write_file")
        
        # Test read_file
        result = executor.read_file(test_file)
        if not result["success"] or result["content"] != "test content":
            print(f"  ❌ read_file failed: {result}")
            return False
        print("  ✅ read_file")
        
        # Test execute_bash
        result = executor.execute_bash("echo 'hello'")
        if not result["success"] or "hello" not in result["stdout"]:
            print(f"  ❌ execute_bash failed: {result}")
            return False
        print("  ✅ execute_bash")
        
        # Cleanup
        (project_root / test_file).unlink(missing_ok=True)
        print("  ✅ ToolExecutor tests passed")
        return True
    except Exception as e:
        print(f"  ❌ ToolExecutor test exception: {e}")
        return False


def test_config_loading():
    """Test configuration loading."""
    print("Testing config loading...")
    try:
        config = load_provider_config()
        assert config.orchestrator is not None
        print(f"  ✅ Config loaded (provider: {config.orchestrator.provider})")
    except Exception as e:
        print(f"  ❌ Config loading failed: {e}")
        return False
    return True


def test_task_planner_fallback():
    """Test TaskPlanner fallback behavior."""
    print("Testing TaskPlanner fallback...")
    try:
        config = load_provider_config()
        llm, _ = create_chat_model(config.orchestrator)
        planner = TaskPlanner(llm=llm, system_prompt=None)
        
        # This should use fallback if LLM fails
        tasks = planner.plan("test task")
        assert len(tasks) > 0, "Planner should return at least one task"
        print(f"  ✅ Planner returned {len(tasks)} task(s) (fallback working)")
    except Exception as e:
        print(f"  ❌ TaskPlanner failed: {e}")
        return False
    return True


def test_worker_initialization():
    """Test LocalWorker initialization."""
    print("Testing LocalWorker initialization...")
    try:
        executor = ToolExecutor(working_dir=project_root)
        worker = LocalWorker(
            model="qwen2.5-coder:14b-instruct",
            working_dir=project_root,
            tool_executor=executor,
            verify_outputs=False,
        )
        assert worker._model == "qwen2.5-coder:14b-instruct"
        print("  ✅ LocalWorker initialized")
    except Exception as e:
        print(f"  ❌ LocalWorker initialization failed: {e}")
        return False
    return True


def main():
    """Run all tests."""
    print("Rozet Orchestrator Test Suite\n")
    print("=" * 50)
    
    results = []
    
    results.append(("ToolExecutor", test_tool_executor()))
    results.append(("Config Loading", test_config_loading()))
    results.append(("TaskPlanner Fallback", test_task_planner_fallback()))
    results.append(("Worker Initialization", test_worker_initialization()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

