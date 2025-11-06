"""Analyze prompt validation results and identify issues."""

import json
from pathlib import Path

report_path = Path(__file__).parent / "prompt_validation_report.json"

with report_path.open() as f:
    report = json.load(f)

print("="*60)
print("PROMPT VALIDATION ANALYSIS")
print("="*60)

issues = []

for result in report["results"]:
    scenario = result["scenario"]
    user_input = result["user_input"]
    expected = result["expected_mode"]
    
    print(f"\n{'='*60}")
    print(f"Scenario {scenario}: {user_input}")
    print(f"Expected: {expected}")
    print(f"{'='*60}")
    
    # Check conversational responses
    if "conversational_test" in result:
        conv = result["conversational_test"]
        response = conv["response"]
        
        print(f"\nResponse (length: {conv['length']}):")
        print(f"{response[:300]}...")
        
        # Check for issues
        if expected == "conversational":
            # Issue: Claims no access when it should know workers have access
            if "don't have access" in response.lower() or "cannot access" in response.lower():
                issues.append({
                    "scenario": scenario,
                    "issue": "Claims no filesystem access (should mention workers)",
                    "response_snippet": response[:200]
                })
                print("\n❌ ISSUE: Claims no access!")
            
            # Issue: Wrong model mentioned
            if "gpt-4" in response.lower() and "gpt-5" not in response.lower():
                issues.append({
                    "scenario": scenario,
                    "issue": "Mentions wrong model (GPT-4 instead of GPT-5-nano)",
                    "response_snippet": response[:200]
                })
                print("\n❌ ISSUE: Wrong model mentioned!")
            
            # Issue: Doesn't mention workers/tools
            if expected == "conversational" and "worker" not in response.lower() and "access" in user_input.lower():
                issues.append({
                    "scenario": scenario,
                    "issue": "Doesn't mention workers when asked about access",
                    "response_snippet": response[:200]
                })
                print("\n⚠️  WARNING: Should mention workers")
    
    # Check planning failures
    if "planning_test" in result:
        plan = result["planning_test"]
        if not plan.get("success"):
            issues.append({
                "scenario": scenario,
                "issue": f"Planning failed: {plan.get('error', 'unknown')}",
                "user_input": user_input
            })
            print(f"\n❌ Planning failed: {plan.get('error')}")

print("\n" + "="*60)
print("SUMMARY OF ISSUES")
print("="*60)

if issues:
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. Scenario {issue['scenario']}: {issue['issue']}")
        if 'response_snippet' in issue:
            print(f"   Response: {issue['response_snippet'][:100]}...")
else:
    print("\n✅ No critical issues found!")

print(f"\nTotal issues: {len(issues)}")

