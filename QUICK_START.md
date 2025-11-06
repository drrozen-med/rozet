# Quick Start - Run Rozet Orchestrator

## Fix: ModuleNotFoundError

If you see `ModuleNotFoundError: No module named 'orchestrator'`, set PYTHONPATH:

```bash
export PYTHONPATH=/Users/urirozen/projects/rozet
```

## Easy Ways to Run

### Option 1: Use the convenience script (easiest)
```bash
./run_orchestrator.sh --repl
```

### Option 2: Use orchestrator/run.sh
```bash
./orchestrator/run.sh --repl
```

### Option 3: Manual (set PYTHONPATH)
```bash
cd /Users/urirozen/projects/rozet
source .venv/bin/activate
export PYTHONPATH=.
python orchestrator/cli.py --repl
```

### Option 4: Add to your shell config (permanent fix)
Add this to your `~/.zshrc`:
```bash
# Rozet Orchestrator
export ROZET_ROOT=/Users/urirozen/projects/rozet
alias rozet="cd $ROZET_ROOT && source .venv/bin/activate && export PYTHONPATH=. && python orchestrator/cli.py"
```

Then just run:
```bash
rozet --repl
```

## Quick Test

```bash
# Test it works
export PYTHONPATH=/Users/urirozen/projects/rozet
python orchestrator/cli.py plan "test" --dry-run
```
