# Orchestrator CLI Usage Guide

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /Users/urirozen/projects/rozet
source .venv/bin/activate
```

### 2. Run CLI (Non-Interactive Mode)
```bash
# With arguments (non-interactive)
PYTHONPATH=. python orchestrator/cli.py plan "build a todo app" --dry-run

# With full options
PYTHONPATH=. python orchestrator/cli.py plan "build a todo app" \
  --output-format pretty \
  --max-tasks 4 \
  --log-level INFO
```

### 3. Run CLI (Interactive Mode)
```bash
# Will prompt for request
PYTHONPATH=. python orchestrator/cli.py plan --dry-run

# Or without dry-run (requires API keys)
PYTHONPATH=. python orchestrator/cli.py plan
```

### 4. Via OpenCode Integration
```bash
# From OpenCode CLI
cd opencode
opencode orchestrator plan "build a todo app"
```

## Command Options

### Basic Usage
```bash
python orchestrator/cli.py plan <request> [options]
```

### Arguments
- `plan` - Command to execute (currently only "plan" is supported)
- `<request>` - User request/description (optional if using interactive mode)

### Options
- `--config PATH` - Path to provider config YAML (default: `config/providers.yaml`)
- `--working-dir PATH` - Working directory for execution (default: current directory)
- `--max-tasks N` - Maximum number of tasks to generate (default: 6)
- `--log-level {DEBUG,INFO,WARN,ERROR}` - Logging level (default: INFO)
- `--output-format {json,pretty}` - Output format (default: json)
- `--execute` - Execute tasks after planning (otherwise just plan)
- `--dry-run` - Dry run mode: validate config without making API calls

## Examples

### Test Configuration (Dry-Run)
```bash
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan "test request" --dry-run
```

### Plan Tasks (Requires API Keys)
```bash
export GEMINI_API_KEY="your-key-here"
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan "build a REST API with user authentication"
```

### Plan and Execute
```bash
export GEMINI_API_KEY="your-key-here"
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan "create a simple todo app" --execute
```

### Interactive Mode
```bash
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan
# Will prompt: "Enter your request (or press Ctrl+D to cancel):"
```

### JSON Output
```bash
source .venv/bin/activate
PYTHONPATH=. python orchestrator/cli.py plan "test" --output-format json --dry-run
```

## Environment Variables

### Required for Full Functionality
- `GEMINI_API_KEY` - For Gemini orchestrator
- `ANTHROPIC_API_KEY` - For Anthropic workers
- `OPENAI_API_KEY` - For OpenAI workers

### Optional
- `ORCHESTRATOR_STRICT_CREDENTIALS=false` - Disable strict credential validation (for testing)
- `PYTHONPATH=.` - Set to project root to enable imports

## Troubleshooting

### Import Errors
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=/Users/urirozen/projects/rozet
python orchestrator/cli.py plan "test" --dry-run
```

### Credential Errors
```bash
# Use dry-run mode to test without credentials
python orchestrator/cli.py plan "test" --dry-run

# Or disable strict validation
ORCHESTRATOR_STRICT_CREDENTIALS=false python orchestrator/cli.py plan "test" --dry-run
```

### Virtual Environment
```bash
# If venv not activated
source .venv/bin/activate

# If venv doesn't exist
uv venv
source .venv/bin/activate
uv pip install -r orchestrator/requirements.txt
```

