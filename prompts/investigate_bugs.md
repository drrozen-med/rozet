# INVESTIGATION TASK: Analyze Rozet Orchestrator Bugs

## Your Role
You are a senior debugging engineer investigating critical bugs in the Rozet orchestrator system.

## Tech Stack Context
- **Language:** Python 3.13
- **LLM Integration:** LangChain
- **APIs:** OpenAI/OpenRouter for orchestrator, Ollama (localhost:11434) for workers
- **UI:** Rich library for terminal
- **Config:** YAML files in config/

## Bug Reports from Manual Testing

### Bug #1: 401 "User not found" Authentication Error
**Severity:** P0 Critical - Blocks all conversational features

**Symptoms:**
- Occurs when user types greetings or asks questions
- Error: `openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}`
- Location: `orchestrator/tui.py:107` in `_get_conversational_response()`
- Stack trace ends at: `openai/_base_client.py:1047`

**Current Configuration:**
```yaml
# config/providers.yaml
orchestrator:
  provider: openai
  model: gpt-5-nano
  endpoint: https://openrouter.ai/api/v1
  system_prompt_path: prompts/orchestrator.md

credentials:
  openai: OPENAI_API_KEY
```

**Code Location:**
```python
# orchestrator/tui.py:142
orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)

# orchestrator/tui.py:107 (in _get_conversational_response)
response = llm.invoke(messages)  # <- 401 ERROR HERE
```

**Hypotheses:**
1. Model name "gpt-5-nano" doesn't exist or is incorrect for OpenRouter
2. OPENAI_API_KEY environment variable not set or invalid for OpenRouter
3. Provider/endpoint mismatch (provider=openai but endpoint=OpenRouter)
4. OpenRouter requires different authentication

---

### Bug #2: Ollama Worker Timeout (120s)
**Severity:** P0 Critical - Blocks task execution

**Symptoms:**
- Timeout after exactly 120 seconds during task execution
- Error: `HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)`
- Location: `orchestrator/workers/local_worker.py:171` in `_call_ollama()`
- User experience: Long wait with only spinning indicator, no progress updates

**Test Case:**
- Task: "analyze the orchestrator/tui.py file and identify any error handling issues"
- Execution time: 123.7 seconds (just over 120s limit)
- Result: Timeout failure

**Code Location:**
```python
# orchestrator/workers/local_worker.py:171
response = requests.post(url, json=payload, timeout=120)  # <- HARDCODED 120s
```

**Hypotheses:**
1. Timeout too short for complex analysis tasks
2. No configuration option to adjust timeout
3. Ollama may be slow or model is large
4. No progress indication during execution

---

## Your Task

Analyze both bugs and provide **explicit, step-by-step fix recommendations**.

### Requirements:
1. **Root Cause Analysis:** Explain exactly why each bug occurs
2. **Fix Recommendations:** Provide specific code changes with:
   - File path and line number
   - Current code snippet
   - Replacement code
   - Explanation of why it fixes the issue
3. **Verification Steps:** How to test that the fix works

### Output Format (JSON):

```json
{
  "bugs_analyzed": [
    {
      "bug_id": "401_auth_error",
      "severity": "P0",
      "root_cause": "Detailed explanation of why this happens",
      "affected_files": ["path/to/file.py:line"],
      "environment_check": {
        "required_env_vars": ["OPENAI_API_KEY"],
        "how_to_verify": "command to check",
        "common_issues": ["issue 1", "issue 2"]
      },
      "fix_recommendations": [
        {
          "step": 1,
          "description": "What this fix does",
          "file": "orchestrator/config_loader.py",
          "line_number": 123,
          "current_code": "existing code snippet",
          "new_code": "replacement code snippet",
          "reason": "why this solves the problem"
        }
      ],
      "verification_steps": [
        "Step 1: Do this to verify",
        "Step 2: Expected result"
      ]
    }
  ],
  "additional_recommendations": [
    "Other improvements to consider"
  ]
}
```

## Investigation Guidelines
1. Read the actual code files to understand the full context
2. Check environment variable handling
3. Verify API authentication flow
4. Consider configuration validation
5. Think about user experience improvements

Begin your investigation now.
