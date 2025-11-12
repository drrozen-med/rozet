# Rozet Interactive Testing - Bug Report
**Date:** 2025-11-06
**Tested by:** Claude (automated human-like interaction)

## 🔴 CRITICAL BUGS

### Bug #1: 401 Authentication Error - "User not found"
**Severity:** CRITICAL - Blocks all conversational features
**Occurrence:** Every conversational request (greetings, questions)
**Error:**
```
Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}
```

**Stack Trace:**
```
orchestrator/tui.py:107, in _get_conversational_response
    response = llm.invoke(messages)
...
openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}
```

**Root Cause:**
- Using `openai/gpt-5-nano` model
- API authentication failing with OpenRouter or OpenAI
- Likely incorrect API key or model name

**Impact:**
- ❌ Cannot have conversations
- ❌ Cannot ask questions
- ✅ Task planning still works (falls back to heuristic planner)
- ✅ Task execution still works

---

### Bug #2: Ollama Worker Timeout (120s)
**Severity:** CRITICAL - Blocks task execution
**Occurrence:** When executing tasks with local worker
**Error:**
```
Ollama API failed: HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)
```

**Root Cause:**
- Ollama not running on localhost:11434, OR
- Task taking longer than 120 seconds to complete

**Impact:**
- ❌ Task execution fails
- ⏱️ User waits 2 minutes before seeing error
- No progress indication during execution

**Test Result:**
- Asked: "analyze the orchestrator/tui.py file and identify any error handling issues"
- Execution time: 123.7 seconds (just over timeout)
- Result: ✗ T1 - Ollama API failed

---

## ⚠️ MEDIUM SEVERITY ISSUES

### Issue #1: No Progress Indication During Long Tasks
**Severity:** MEDIUM - UX issue
**Occurrence:** During task execution (120+ seconds)
**Behavior:**
- Shows spinning indicator: `⠋ Executing tasks...`
- No indication of what's happening
- No way to cancel
- User has no idea if it's making progress or stuck

**Suggested Fix:**
- Show which subtask is running
- Show LLM streaming output
- Add cancel button (Ctrl+C handler)
- Add timeout warnings at 30s, 60s, 90s

---

### Issue #2: Observability Connection Failures (Non-blocking)
**Severity:** LOW - Logging noise
**Occurrence:** Every event (TaskPlanned, TaskAssigned, WorkerCompleted)
**Error:**
```
Failed to send observability event: HTTPConnectionPool(host='localhost', port=4000): Connection refused
```

**Root Cause:** Observability service not running

**Impact:**
- ❌ Logs are noisy
- ✅ Doesn't block functionality

**Suggested Fix:**
- Make observability optional
- Suppress warnings if service unavailable
- Add config flag: `ENABLE_OBSERVABILITY=false`

---

### Issue #3: LangChain Deprecation Warning
**Severity:** LOW - Future compatibility
**Warning:**
```
LangChainDeprecationWarning: Please see the migration guide at:
https://python.langchain.com/docs/versions/migrating_memory/
  self._memory = ConversationSummaryBufferMemory(
```

**Location:** `orchestrator/core/context_manager.py:69`

**Impact:**
- ⚠️ Will break in future LangChain versions
- Currently works but deprecated

---

## ✅ WHAT WORKS

### Task Planning
- ✅ Heuristic fallback planner works when API fails
- ✅ Creates reasonable single-task plans
- ✅ Identifies correct files
- ✅ Plans in < 1 second

### Interactive Prompts
- ✅ "Execute tasks? [y/n]" works correctly
- ✅ Validates user input (rejects invalid responses)
- ✅ Returns to prompt after execution

### REPL Startup
- ✅ Starts in ~1-2 seconds
- ✅ Shows welcome message clearly
- ✅ Displays current model
- ✅ Helpful tip message

### Help Command
- ✅ Shows available commands
- ✅ Clean formatting
- ✅ Returns to prompt correctly

---

## 🎯 USER EXPERIENCE OBSERVATIONS

### Positive
1. **Clean UI** - Colors, boxes, and spinners look great
2. **Fast startup** - 1-2 seconds is excellent
3. **Clear prompts** - `You:` is intuitive
4. **Graceful fallback** - Heuristic planner works when API fails

### Negative
1. **Long silences** - 120 seconds with no feedback is frustrating
2. **No cancel option** - Can't interrupt long tasks
3. **Error messages unclear** - "401 User not found" is cryptic (which user?)
4. **No recovery** - After 401 error, REPL continues but feature is broken

---

## 📊 RESPONSE TIMES

| Action | Expected | Actual | Status |
|--------|----------|--------|--------|
| Startup | <3s | 1.2s | ✅ Excellent |
| Greeting | <3s | 2.0s | ⚠️ Failed (401) |
| Help | <1s | <1s | ✅ Fast |
| Plan task | <5s | 1.0s | ✅ Fast |
| Execute task | <30s | 123.7s | ❌ Timeout |
| File creation | <10s | (not tested, 401 error) | ❌ |

---

## 🔧 PRIORITY FIXES

### P0 (Urgent - Blocks Core Functionality)
1. **Fix 401 authentication error**
   - Check API key configuration
   - Verify model name `openai/gpt-5-nano` is correct
   - Test with OpenRouter vs OpenAI API

2. **Fix Ollama timeout**
   - Increase timeout or make configurable
   - Add progress streaming
   - Better error handling

### P1 (Important - UX Issues)
3. **Add progress indication during execution**
   - Stream LLM output
   - Show current subtask
   - Add estimated time remaining

4. **Add cancel/interrupt handler**
   - Ctrl+C to cancel task
   - Graceful shutdown
   - Don't corrupt state

### P2 (Nice to Have)
5. **Suppress observability warnings** when service unavailable
6. **Migrate LangChain memory** to non-deprecated API
7. **Better error messages** (explain what "User not found" means)

---

## 📋 TEST COVERAGE

### Tested ✅
- [x] REPL startup
- [x] Help command
- [x] Task planning
- [x] Interactive y/n prompts
- [x] Task execution (failed, but tested)
- [x] Conversational input (failed, but tested)

### Not Tested ❌
- [ ] Successful task execution (blocked by timeout)
- [ ] File operations
- [ ] Multi-task plans
- [ ] Exit command
- [ ] Empty input handling
- [ ] Long response handling

---

## 🧪 NEXT STEPS

1. **Fix P0 bugs** (401, timeout)
2. **Re-run full test suite** to verify fixes
3. **Test remaining scenarios** (file creation, multi-task, exit)
4. **Add automated regression tests** to prevent future breakage

---

## 💡 RECOMMENDATIONS

### Configuration
- Make API provider configurable (OpenRouter vs OpenAI vs Ollama only)
- Add `--debug` flag for verbose logging
- Add `--timeout` flag for customizable timeouts

### Error Handling
- Catch 401 errors and show helpful message:
  ```
  ❌ Authentication failed. Please check your API key in:
     - OPENAI_API_KEY environment variable
     - config.yml file
  ```

### UX Improvements
- Add streaming responses (show text as it's generated)
- Add "Thinking... (15s elapsed)" progress updates
- Add Ctrl+C handler with confirmation: "Cancel task? [y/n]"

---

**Testing Method:** Automated human-like interaction using `pexpect`
**Test Script:** `scripts/rozet_tests_self.py`
**Full Output:** `/tmp/rozet_self_test_v2.log`
