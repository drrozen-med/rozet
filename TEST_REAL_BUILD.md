# Real Build Test - Using Rozet to Build Itself

**Goal:** Test the full orchestrator system by having it build a real, useful piece of software for the project.

## Test Plan

1. **Request:** "Create a health check script that verifies the orchestrator system is properly configured"
2. **Expected:** Orchestrator should:
   - Plan the task (create health check script)
   - Execute via worker
   - Verify the script works
   - Report success

## What We'll Build

A `health_check.py` script that:
- Checks if API keys are configured
- Verifies config files exist
- Tests model connectivity
- Reports system status

This is a real, useful tool for the project!

## Running the Test

```bash
./rozet --repl
# Then: "Create a health check script that verifies the orchestrator system is properly configured"
```

Let's see if the system can actually build software!

