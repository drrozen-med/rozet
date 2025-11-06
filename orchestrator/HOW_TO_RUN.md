# How to Run Rozet Orchestrator

## Quick Start

### 1. Setup Environment
```bash
cd /Users/urirozen/projects/rozet
source .venv/bin/activate
export PYTHONPATH=.
export OPENAI_API_KEY='your-openai-api-key'  # Required for GPT-5-nano orchestrator
```

### 2. Run Interactive REPL (Recommended)
```bash
# Start conversational REPL interface
python orchestrator/cli.py --repl

# Or use the convenience script
./orchestrator/run.sh
```

### 3. Plan Tasks (Non-Interactive)
```bash
# Just plan (no execution)
python orchestrator/cli.py plan "Create a Python script hello.py that prints 'Hello, World!'"

# Plan and execute
python orchestrator/cli.py plan "Create hello.py" --execute

# Dry run (no API calls, just validate)
python orchestrator/cli.py plan "test" --dry-run
```

## Usage Examples

### Interactive REPL Mode
```bash
python orchestrator/cli.py --repl
# Then type your requests interactively:
# > Create a todo app
# > Add user authentication
# > Write tests
```

### Plan Only (See what tasks would be created)
```bash
python orchestrator/cli.py plan "Build a REST API with authentication" \
  --max-tasks 5 \
  --output-format pretty
```

### Plan and Execute
```bash
python orchestrator/cli.py plan "Create hello.py with print statement" \
  --execute \
  --working-dir ./my-project
```

### With Custom Config
```bash
python orchestrator/cli.py plan "test" \
  --config config/custom-providers.yaml \
  --log-level DEBUG
```

## Command Options

```
python orchestrator/cli.py [command] [request] [options]

Commands:
  plan              Plan tasks from user request

Options:
  --repl, --tui     Start interactive REPL chat interface
  --execute         Execute tasks after planning
  --dry-run         Validate config without API calls
  --config PATH     Custom config file (default: config/providers.yaml)
  --working-dir DIR Working directory (default: current directory)
  --max-tasks N     Max tasks to generate (default: 6)
  --log-level LEVEL DEBUG|INFO|WARN|ERROR (default: WARN)
  --output-format   json|pretty (default: pretty)
```

## Current Configuration

- **Orchestrator**: GPT-5-nano (via OpenRouter) - Fast, affordable, 400K context
- **Workers**: Ollama (Qwen 2.5 Coder 14B) - Local, free
- **Config**: `config/providers.yaml`

## Environment Variables

**Required:**
- `OPENAI_API_KEY` - For GPT-5-nano orchestrator (via OpenRouter)

**Optional:**
- `ORCHESTRATOR_USE_REAL_API=true` - Enable real API calls in tests
- `PYTHONPATH=.` - Set to project root (already in run.sh)

## Troubleshooting

### Module Not Found
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=/Users/urirozen/projects/rozet
python orchestrator/cli.py --help
```

### Ollama Not Available
- Worker will try Ollama, but tests will skip gracefully if unavailable
- Check: `ollama list` to see available models
- Pull model: `ollama pull qwen2.5-coder:14b-instruct`

### API Key Issues
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Set it if missing
export OPENAI_API_KEY='your-key-here'
```

## Test It

```bash
# Quick test (dry run)
python orchestrator/cli.py plan "test" --dry-run

# Real test (requires API key)
python orchestrator/cli.py plan "Create test.txt with 'Hello'" --execute
```

