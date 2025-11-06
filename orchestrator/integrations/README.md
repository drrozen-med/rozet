# OpenCode Integration Status

## Overview

The `opencode_bridge.py` module provides a bridge between OpenCode's session system and our Rozet orchestrator. This allows Rozet to leverage OpenCode's tools (read, write, bash, etc.) while maintaining our REPL interface and task planning capabilities.

## Current Status

✅ **Bridge Module Created**: Basic structure in place  
🔄 **OpenCode SDK Integration**: Partial (SDK available but full API integration pending)  
⏳ **Session Management**: Mock implementation (needs full OpenCode API)  
⏳ **Tool Execution**: Not yet implemented  

## Architecture

```
User Request
    ↓
Rozet REPL (orchestrator/tui.py)
    ↓
OpenCode Session Bridge (integrations/opencode_bridge.py)
    ├── Task Planning (orchestrator/core/task_planner.py)
    ├── Context Management (orchestrator/core/context_manager.py)
    └── OpenCode Session (opencode SDK)
        └── Tool Execution (read, write, bash, etc.)
```

## How It Works

1. **User sends request** → Rozet REPL
2. **REPL routes** → OpenCode Session Bridge
3. **Bridge plans tasks** → Task Planner (GPT-5-nano)
4. **Bridge executes** → OpenCode tools (via session)
5. **Results aggregated** → Returned to user

## Next Steps

1. **Full OpenCode API Integration**
   - Implement session creation via OpenCode API
   - Implement message sending/receiving
   - Implement tool execution

2. **Tool Routing**
   - Map orchestrator tasks to OpenCode tools
   - Handle tool results and errors
   - Aggregate results

3. **Session Management**
   - Create/manage OpenCode sessions
   - Sync session state with orchestrator context
   - Handle session lifecycle

## Usage

```python
from orchestrator.integrations.opencode_bridge import OpenCodeSessionBridge

# Initialize bridge
bridge = OpenCodeSessionBridge(working_dir=Path("/path/to/project"))

# Create session
session_id = bridge.create_session()

# Handle request
result = bridge.handle_user_request("Create a Python script that prints hello")
```

## Dependencies

- OpenCode SDK (optional - bridge works without it)
- OpenCode server running (for full integration)
- Our orchestrator components (always required)

## Testing

Run integration tests:
```bash
pytest orchestrator/tests/integration/test_opencode_bridge.py -v
```

Note: Full integration tests require OpenCode server to be running.

