"""Test harness for validating orchestrator prompt behavior across conversation scenarios.

This script tests 10 different conversation starters to ensure the orchestrator:
- Responds conversationally to simple questions (no task plans)
- Creates task plans only when multi-step work is required
- Demonstrates awareness of its capabilities
- Follows the prompt guidelines correctly
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model


# Test scenarios: (user_input, expected_mode, expected_characteristics)
TEST_SCENARIOS: List[Tuple[str, str, List[str]]] = [
    # 1. Simple greeting - should be conversational, NO task plan
    (
        "hello",
        "conversational",
        ["no task plan", "greeting", "friendly"],
    ),
    # 2. Capability question - should answer directly, confirm access, NO task plan
    (
        "do you have access to the local codebase?",
        "conversational",
        ["no task plan", "confirms access", "mentions workers"],
    ),
    # 3. Simple status check - should be conversational
    (
        "what model are you using?",
        "conversational",
        ["no task plan", "mentions model", "direct answer"],
    ),
    # 4. Factual question - should answer directly
    (
        "what files are in the prompts directory?",
        "conversational_or_plan",
        ["may list files", "no unnecessary task plan"],
    ),
    # 5. Task request - SHOULD create task plan
    (
        "create a README.md file in the root directory",
        "task_plan",
        ["task plan", "T1", "description", "files", "success criteria"],
    ),
    # 6. Multi-step task - SHOULD create task plan with multiple tasks
    (
        "refactor the orchestrator prompt to add examples section",
        "task_plan",
        ["task plan", "multiple tasks", "T1", "T2", "files mentioned"],
    ),
    # 7. Ambiguous request - should ask for clarification OR create plan
    (
        "fix the bug",
        "clarification_or_plan",
        ["asks questions", "or", "creates diagnostic plan"],
    ),
    # 8. Documentation request - should create task plan
    (
        "write documentation for the ToolExecutor class",
        "task_plan",
        ["task plan", "documentation", "files"],
    ),
    # 9. Testing request - should create task plan
    (
        "add unit tests for the task planner",
        "task_plan",
        ["task plan", "tests", "test_", "files"],
    ),
    # 10. Complex multi-file task - should create structured plan
    (
        "implement file locking for multi-agent operations",
        "task_plan",
        ["task plan", "multiple tasks", "file_locking", "dependencies"],
    ),
]


def test_conversational_response(
    llm, user_input: str, context_manager: ConversationContextManager, system_prompt: str
) -> dict:
    """Test if orchestrator responds conversationally (no task plan)."""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Get context summary
    context_summary = context_manager.summarize_old_messages()
    
    # Build messages with system prompt
    messages = [SystemMessage(content=system_prompt)]
    if context_summary:
        messages.append(HumanMessage(content=f"Context: {context_summary}"))
    messages.append(HumanMessage(content=user_input))
    
    response = llm.invoke(messages)
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    # Check if it's conversational (no task plan structure)
    has_task_plan = any(
        marker in response_text.lower()
        for marker in ["task t1", "task t2", "## plan", "planned tasks", "task_id", '"task_id"', '"tasks"']
    )
    
    return {
        "response": response_text,
        "is_conversational": not has_task_plan,
        "length": len(response_text),
        "mentions_workers": "worker" in response_text.lower(),
        "mentions_access": any(word in response_text.lower() for word in ["access", "file", "read", "write"]),
        "mentions_tools": any(word in response_text.lower() for word in ["tool", "executor", "bash", "filesystem"]),
    }


def test_task_planning(
    planner: TaskPlanner, user_input: str, context_manager: ConversationContextManager
) -> dict:
    """Test if orchestrator creates appropriate task plan."""
    context_summary = context_manager.summarize_old_messages()
    
    try:
        tasks = planner.plan(user_input, context_summary=context_summary)
        
        return {
            "success": True,
            "task_count": len(tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "files": t.files,
                    "success_criteria_count": len(t.success_criteria),
                    "has_dependencies": len(t.dependencies) > 0,
                }
                for t in tasks
            ],
            "all_have_files": all(len(t.files) > 0 for t in tasks),
            "all_have_criteria": all(len(t.success_criteria) > 0 for t in tasks),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "task_count": 0,
        }


def run_test_scenario(
    scenario_idx: int,
    user_input: str,
    expected_mode: str,
    expected_chars: List[str],
    llm,
    planner: TaskPlanner,
    context_manager: ConversationContextManager,
    system_prompt: str,
) -> dict:
    """Run a single test scenario and return results."""
    print(f"\n{'='*60}")
    print(f"Test {scenario_idx + 1}: {user_input[:50]}...")
    print(f"Expected: {expected_mode}")
    print(f"{'='*60}\n")
    
    result = {
        "scenario": scenario_idx + 1,
        "user_input": user_input,
        "expected_mode": expected_mode,
        "expected_characteristics": expected_chars,
    }
    
    # Test conversational response
    if expected_mode in ("conversational", "conversational_or_plan"):
        conv_result = test_conversational_response(llm, user_input, context_manager, system_prompt)
        result["conversational_test"] = conv_result
        
        # Record in context
        context_manager.record_user(user_input)
        context_manager.record_assistant(conv_result["response"])
    
    # Test task planning
    if expected_mode in ("task_plan", "conversational_or_plan", "clarification_or_plan"):
        plan_result = test_task_planning(planner, user_input, context_manager)
        result["planning_test"] = plan_result
        
        if plan_result.get("success"):
            # Record planning result
            planning_summary = f"Planned {plan_result['task_count']} tasks"
            context_manager.record_user(user_input)
            context_manager.record_assistant(planning_summary)
    
    return result


def main():
    """Run all test scenarios and generate report."""
    print("Loading configuration...")
    config = load_provider_config()
    
    print("Creating orchestrator LLM...")
    orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
    
    print("Initializing context manager...")
    context_manager = ConversationContextManager(
        llm=orchestrator_llm,
        storage_path=Path.cwd() / ".opencode" / "test_context.jsonl",
    )
    
    print("Creating task planner...")
    # TaskPlanner uses its own JSON-focused prompt, not the orchestrator's conversational prompt
    planner = TaskPlanner(
        llm=orchestrator_llm,
        system_prompt=None,  # Use DEFAULT_SYSTEM_PROMPT (JSON-focused)
    )
    
    print("\n" + "="*60)
    print("RUNNING PROMPT VALIDATION TESTS")
    print("="*60)
    
    results = []
    for idx, (user_input, expected_mode, expected_chars) in enumerate(TEST_SCENARIOS):
        result = run_test_scenario(
            idx, user_input, expected_mode, expected_chars,
            orchestrator_llm, planner, context_manager, system_prompt
        )
        results.append(result)
        
        # Small delay to avoid rate limits
        import time
        time.sleep(1)
    
    # Generate report
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    report = {
        "total_tests": len(results),
        "results": results,
    }
    
    # Save detailed report
    report_path = Path.cwd() / "orchestrator" / "tests" / "prompt_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Print summary
    print("\nQuick Summary:")
    for result in results:
        mode = result["expected_mode"]
        print(f"\nTest {result['scenario']}: {result['user_input'][:40]}...")
        print(f"  Expected: {mode}")
        
        if "conversational_test" in result:
            conv = result["conversational_test"]
            print(f"  Conversational: {conv['is_conversational']} (length: {conv['length']})")
        
        if "planning_test" in result:
            plan = result["planning_test"]
            if plan.get("success"):
                print(f"  Planning: {plan['task_count']} tasks created")
            else:
                print(f"  Planning: FAILED - {plan.get('error', 'unknown')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

