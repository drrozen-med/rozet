# Orchestrator TUI Usage

## 🎨 Interactive TUI Chat Interface

The orchestrator now supports a **rich, interactive TUI** (Text User Interface) just like OpenCode!

### Quick Start

```bash
# Activate venv
cd /Users/urirozen/projects/rozet
source .venv/bin/activate

# Start TUI
PYTHONPATH=. python orchestrator/cli.py --tui
```

### Features

- ✅ **Beautiful Rich TUI** - Colorful, formatted interface
- ✅ **Two-way chat** - Conversation-style interaction
- ✅ **Task planning** - See tasks in formatted panels
- ✅ **Task execution** - Execute plans interactively
- ✅ **Context persistence** - Maintains conversation history
- ✅ **Observability** - Events sent to observability system

### TUI Commands

- `help` - Show available commands
- `plan <request>` - Plan tasks for your request
- `exit` / `quit` / `q` - Exit the TUI

### Example Session

```
╭───────────────────── Welcome ─────────────────────╮
│ Orchestrator TUI                                  │
│ Chat with your multi-agent orchestrator           │
│ Type 'exit' or 'quit' to end, 'help' for commands │
╰───────────────────────────────────────────────────╯

✓ Orchestrator ready!

You: build a todo app

✓ Planned Tasks:

╭────── Task T1 ──────╮
│ Description: Build  │
│ backend API         │
│ Files: api.py       │
│ Success Criteria:   │
│   • REST endpoints  │
╰─────────────────────╯

Execute tasks? [y/N]: y

✓ Execution Results:
  ✓ T1
    Modified: api.py
```

### Comparison: CLI vs TUI

**CLI Mode (one-shot):**
```bash
python orchestrator/cli.py plan "build todo app" --execute
```

**TUI Mode (interactive chat):**
```bash
python orchestrator/cli.py --tui
# Then chat interactively
```

Both modes are available - use CLI for automation, TUI for interactive development!

