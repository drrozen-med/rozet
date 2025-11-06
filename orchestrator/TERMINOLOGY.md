# Terminal Interface Terminology

## Types of Terminal Interfaces

### 1. **CLI (Command Line Interface)**
- **Fixed commands** with arguments/flags
- Example: `git commit -m "message"` or `python orchestrator/cli.py plan "request"`
- One-shot execution
- No interactive context

### 2. **REPL (Read-Eval-Print Loop)** ⬅️ *This is what Claude Code & Gemini CLI are*
- **Interactive conversation loop**
- No fixed UI structure - just input/output
- Previous text scrolls up naturally
- Example: Python REPL, Node.js REPL, Claude Code, Gemini CLI
- **Pattern**: Type → Get response → Type again → ...
- Conversation flows naturally, older text moves up

### 3. **TUI (Text User Interface)** ⬅️ *This is what OpenCode moved to*
- **Fixed structured interface** with panels/windows
- Uses libraries like `rich`, `textual`, `blessed`
- Has menus, forms, structured layouts
- Example: OpenCode's new interface, `htop`, `vtop`
- **Pattern**: Fixed layout, panels, doesn't scroll naturally
- More like a GUI but in text

## What We Built

Our current `orchestrator/tui.py` is actually a **REPL**, not a TUI!

- ✅ Interactive conversation loop
- ✅ Natural scrolling (previous text moves up)
- ✅ No fixed UI structure
- ✅ Type → Response → Type again

**We should rename it** to reflect this:
- `orchestrator/repl.py` - Interactive REPL mode
- `orchestrator/cli.py` - Fixed CLI commands
- (Future) `orchestrator/tui.py` - Fixed TUI like OpenCode

## Comparison

| Type | Example | Flow | UI Structure |
|------|---------|------|-------------|
| **CLI** | `git commit` | One-shot | None |
| **REPL** | Claude Code, Gemini CLI | Loop | None (natural scroll) |
| **TUI** | OpenCode (new), htop | Fixed panels | Structured |

## Current Commands

```bash
# CLI mode (fixed commands)
python orchestrator/cli.py plan "request"

# REPL mode (what we call "TUI" but is actually REPL)
python orchestrator/cli.py --tui  # Should be --repl
```

## Recommendation

1. Rename `--tui` flag to `--repl` or `--interactive`
2. Keep `tui.py` for now but document it as REPL
3. Future: Build actual TUI (like OpenCode) with fixed panels

