# Manual REPL Testing Guide

## Why Manual Testing?

Unit tests verify code works, but **manual testing** verifies the **user experience** - how it feels to actually use the REPL like a human would.

## How to Test Manually

### 1. Start the REPL

```bash
rozett --repl
# Or
./rozet --repl
```

### 2. Test Scenarios

#### Scenario A: Greetings & Small Talk
```
You: hello
Expected: Friendly greeting response

You: how are you?
Expected: Conversational response

You: thanks
Expected: Acknowledgment
```

#### Scenario B: Simple Task
```
You: create a file test.txt with hello
Expected: 
  - Task planned
  - File created
  - Success message
```

#### Scenario C: Complex Task
```
You: build a todo app with FastAPI backend and React frontend
Expected:
  - Multiple tasks planned
  - Clear task breakdown
  - Option to execute
```

#### Scenario D: Commands
```
You: help
Expected: List of available commands

You: exit
Expected: Clean exit
```

#### Scenario E: Edge Cases
```
You: (empty input)
Expected: Prompt again or error message

You: asdfghjkl (nonsense)
Expected: Graceful handling

You: create a script that does everything
Expected: Reasonable task breakdown
```

## Automated Component Tests

We have `scripts/test_repl_manual.py` which tests REPL components programmatically, but **true manual testing** requires:

1. **Actually typing** in the terminal
2. **Reading responses** like a human would
3. **Noticing UX issues** (slow responses, unclear messages, etc.)
4. **Testing error handling** (what happens when things go wrong?)

## What to Look For

### ✅ Good UX
- Clear prompts
- Fast responses (< 3s for simple tasks)
- Helpful error messages
- Natural conversation flow
- Easy to exit

### ❌ Bad UX
- Confusing prompts
- Slow responses (> 10s)
- Cryptic error messages
- Broken conversation flow
- Hard to exit

## Current Status

**Automated Tests:** ✅ 24/24 unit tests passing  
**Component Tests:** ✅ REPL components tested  
**Manual Testing:** ⚠️ **NEEDS TO BE DONE**

## Next Steps

1. **Actually run the REPL** and test each scenario above
2. **Document findings** - what works, what doesn't
3. **Fix UX issues** discovered
4. **Repeat** until UX is smooth

## Quick Test Script

```bash
# Test 1: Start REPL
rozett --repl

# Then manually type:
hello
create a file test.txt
help
exit
```

**This is the only way to truly validate the user experience!**

