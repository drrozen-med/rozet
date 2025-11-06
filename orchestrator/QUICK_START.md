# Orchestrator Quick Start

## Easy Usage (Defaults Applied)

### Method 1: Simple Wrapper (Recommended)
```bash
cd /Users/urirozen/projects/rozet
./orchestrator/run.sh
# If interactive terminal → starts TUI automatically
# Otherwise → runs CLI with your args
```

### Method 2: Direct with Defaults
```bash
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py --tui
# TUI by default (no API keys needed for testing)
```

### Method 3: One-liner Planning
```bash
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan "your request"
# Uses pretty format by default, only warnings shown
```

## Defaults Applied

✅ **Output format**: `pretty` (was `json`)  
✅ **Log level**: `WARN` (was `INFO`) - less noise  
✅ **Config**: Auto-finds `config/providers.yaml`  
✅ **Working dir**: Current directory  
✅ **TUI mode**: Available with `--tui` flag  

## Quick Commands

```bash
# TUI chat interface
python orchestrator/cli.py --tui

# Quick plan (pretty output)
python orchestrator/cli.py plan "build a todo app"

# JSON output (when needed)
python orchestrator/cli.py plan "request" --output-format json

# With execution
python orchestrator/cli.py plan "request" --execute
```

## API Keys

Set these environment variables:
```bash
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  # Optional
export OPENAI_API_KEY="your-key"      # Optional
```

Or create `config/providers.yaml` from `config/providers.example.yaml` and configure credentials there.

