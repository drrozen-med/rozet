# Manual REPL Testing Plan

## ⚠️ Critical Gap Identified

**Current Status:**
- ✅ 24/24 unit tests passing
- ✅ Component tests passing
- ❌ **NO actual manual usage testing done**

**Problem:** Unit tests verify code works, but don't verify **user experience** - how it feels to actually use the REPL like a human would.

## Required Manual Tests

### Test 1: Basic REPL Startup
**Action:** Run `rozett --repl`  
**Expected:**
- [ ] REPL starts without errors
- [ ] Welcome message displays correctly
- [ ] Prompt appears and waits for input
- [ ] No confusing error messages

### Test 2: Greeting Interaction
**Action:** Type `hello` and press Enter  
**Expected:**
- [ ] Friendly greeting response
- [ ] Response appears quickly (< 3 seconds)
- [ ] Response is natural and conversational
- [ ] No errors or stack traces

### Test 3: Help Command
**Action:** Type `help` and press Enter  
**Expected:**
- [ ] Help text displays clearly
- [ ] Commands are listed
- [ ] Formatting is readable
- [ ] Returns to prompt after

### Test 4: Simple Task
**Action:** Type `create a file test.txt with hello world`  
**Expected:**
- [ ] Task is planned (shows task breakdown)
- [ ] Planning happens quickly (< 5 seconds)
- [ ] Task description is clear
- [ ] Option to execute appears
- [ ] If executed, file is actually created
- [ ] Success message is clear

### Test 5: Complex Task
**Action:** Type `build a todo app with FastAPI backend`  
**Expected:**
- [ ] Multiple tasks planned
- [ ] Tasks are logically broken down
- [ ] Task dependencies make sense
- [ ] Can see all tasks before executing

### Test 6: Error Handling
**Action:** Type `asdfghjkl` (nonsense)  
**Expected:**
- [ ] Graceful handling (no crash)
- [ ] Helpful error message
- [ ] Returns to prompt
- [ ] Can continue using REPL

### Test 7: Empty Input
**Action:** Press Enter without typing anything  
**Expected:**
- [ ] Prompt appears again
- [ ] No error message
- [ ] Can continue normally

### Test 8: Exit Command
**Action:** Type `exit`  
**Expected:**
- [ ] Clean exit message
- [ ] Returns to shell
- [ ] No hanging processes
- [ ] Can restart REPL after

### Test 9: Conversation Flow
**Action:** Multiple interactions:
1. `hello`
2. `create a Python script`
3. `thanks`
4. `exit`

**Expected:**
- [ ] Each response is appropriate
- [ ] Context is maintained
- [ ] Flow feels natural
- [ ] No confusion between commands

### Test 10: Long Response
**Action:** Type `explain how Python works`  
**Expected:**
- [ ] Response appears (may be long)
- [ ] Text wraps properly
- [ ] Can read full response
- [ ] No truncation issues

## What to Document

For each test, document:
1. **What happened** - Actual behavior
2. **What should happen** - Expected behavior
3. **Issues found** - UX problems, bugs, confusion
4. **Time taken** - Response times
5. **Error messages** - If any, are they helpful?

## Current Known Issues (from automated tests)

- ⚠️ Worker timeouts (120s) - affects execution
- ⚠️ API authentication (401) - affects planning
- ⚠️ Fallback planner works but may not be optimal

## Next Steps

1. **Actually run the REPL** - `rozett --repl`
2. **Test each scenario above** - Type commands like a human
3. **Document findings** - What works, what doesn't
4. **Fix UX issues** - Make it smooth
5. **Repeat** - Until UX is excellent

## Testing Checklist

Print this and check off as you test:

```
[ ] Test 1: Basic REPL Startup
[ ] Test 2: Greeting Interaction  
[ ] Test 3: Help Command
[ ] Test 4: Simple Task
[ ] Test 5: Complex Task
[ ] Test 6: Error Handling
[ ] Test 7: Empty Input
[ ] Test 8: Exit Command
[ ] Test 9: Conversation Flow
[ ] Test 10: Long Response
```

**This manual testing is essential and cannot be automated!**

