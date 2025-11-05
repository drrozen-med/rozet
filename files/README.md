# Behavioral Engineering Framework

A modular system for creating AI agents with production-grade behaviors - preventing laziness, overconfidence, and untested claims.

## Architecture Overview

```
behavioral-framework/
├── core/                    # Core behavioral patterns
├── integrations/           # Tool-specific behaviors  
├── templates/              # Agent templates
├── config/                 # JSON configurations
└── composer/               # Build system prompts
```

## Quick Start

### 1. Compose an Agent

```bash
# Generate a local coder agent with all safety features
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility,verification \
  --integrations mcp-devtools,bash-tool \
  --output agents/local-coder.md
```

### 2. Configure Behavior Intensity

Edit `config/behavior-settings.json`:

```json
{
  "verification_strictness": "paranoid",  // relaxed, normal, paranoid
  "communication_style": "error-first",   // verbose, balanced, error-first
  "testing_requirement": "mandatory"      // optional, encouraged, mandatory
}
```

### 3. Use in Your Agent

```markdown
<!-- In your agent's system prompt -->
{{include: behavioral-framework/core/anti-laziness.md}}
{{include: behavioral-framework/core/humility-protocol.md}}
{{include: behavioral-framework/integrations/mcp-devtools.md}}
```

## Core Behavioral Modules

| Module | Purpose | Prevents |
|--------|---------|----------|
| `anti-laziness.md` | Enforces complete implementations | TODO comments, partial work |
| `humility-protocol.md` | Requires humble language | False victory claims |
| `ownership-taking.md` | Enforces responsibility | Blaming tools/environment |
| `verification-loops.md` | Mandates testing | Untested claims |
| `error-first-communication.md` | Prioritizes error reporting | Buried errors |
| `suspicion-protocol.md` | Assumes failure until proven | Over-optimistic assumptions |

## Integration Modules

| Module | Purpose | Use Case |
|--------|---------|----------|
| `mcp-devtools.md` | Browser verification | Web/UI development |
| `bash-tool.md` | Command execution patterns | System operations |
| `file-operations.md` | File safety protocols | Code writing |
| `test-execution.md` | Testing requirements | Quality assurance |

## Configuration System

### Behavior Settings (`config/behavior-settings.json`)

Controls the intensity and requirements of behavioral patterns:

```json
{
  "verification": {
    "read_after_write": true,
    "test_after_implement": true,
    "multi_layer_check": true
  },
  "communication": {
    "forbidden_phrases": ["successfully", "done", "working"],
    "required_patterns": ["attempting", "output shows", "verified by"],
    "error_priority": "highest"
  },
  "tool_usage": {
    "bash": {
      "show_output": "always",
      "check_exit_code": true
    },
    "file": {
      "verify_write": true,
      "read_back": true
    }
  }
}
```

### Communication Rules (`config/communication-rules.json`)

Defines language patterns and output formats:

```json
{
  "forbidden_phrases": [
    "successfully implemented",
    "all tests pass",
    "the bug is fixed",
    "this will work",
    "perfect",
    "done"
  ],
  "required_phrases": [
    "attempting",
    "output shows",
    "verified by",
    "testing now",
    "based on the error"
  ],
  "output_format": {
    "error_first": true,
    "show_commands": true,
    "show_outputs": true,
    "checklist_for_claims": true
  }
}
```

### Verification Requirements (`config/verification-requirements.json`)

Specifies what must be verified and how:

```json
{
  "file_operations": {
    "write": ["read_back", "syntax_check"],
    "edit": ["diff_review", "test_affected"],
    "delete": ["backup_first", "confirm_twice"]
  },
  "code_changes": {
    "new_function": ["unit_test", "integration_test"],
    "bug_fix": ["reproduce_first", "verify_fix"],
    "refactor": ["behavior_unchanged"]
  },
  "api_endpoints": {
    "new_endpoint": ["curl_test", "status_check", "response_validation"],
    "modified_endpoint": ["regression_test", "integration_check"]
  }
}
```

## Agent Templates

### Base Agent Template

All agents inherit from `templates/base-agent.md`:

```markdown
# Base Agent Configuration
- Core identity
- Behavioral rules (composable)
- Tool usage patterns
- Communication protocols
```

### Specialized Templates

- **Local Coder Agent**: For running on your GPU (Qwen, etc.)
- **Cloud Reasoner Agent**: For complex analysis (Claude, GPT-4)
- **Test Agent**: Specialized for testing and QA
- **Research Agent**: For documentation/web search
- **Sub-Agent Base**: Template for spawned sub-agents

## Composability Example

Create a paranoid local coder:

```bash
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors ALL \
  --integrations ALL \
  --config-override '{"verification_strictness": "paranoid"}' \
  --output agents/paranoid-coder.md
```

Create a fast-and-loose research agent:

```bash
python composer/agent-composer.py \
  --template templates/research-agent.md \
  --behaviors humility,error-first \
  --integrations bash-tool \
  --config-override '{"verification_strictness": "relaxed"}' \
  --output agents/fast-researcher.md
```

## Usage in OpenCode

### 1. Static Inclusion (Simple)

```markdown
<!-- In .opencode/agents/coder.md -->

# Coder Agent

{{include: behavioral-framework/core/anti-laziness.md}}
{{include: behavioral-framework/core/verification-loops.md}}
{{include: behavioral-framework/integrations/bash-tool.md}}

## Your Custom Instructions
...
```

### 2. Dynamic Composition (Advanced)

```python
# In your orchestrator
from composer.prompt_builder import PromptBuilder

builder = PromptBuilder()
builder.add_template('templates/local-coder-agent.md')
builder.add_behaviors(['anti-laziness', 'humility', 'verification'])
builder.add_integrations(['mcp-devtools', 'bash-tool'])
builder.set_config('config/behavior-settings.json')

prompt = builder.build()
```

## Adjusting Behavior

### Quick Tweaks

Edit config files without touching core modules:

```json
// Make verification less strict
{
  "verification_strictness": "normal"  // was "paranoid"
}
```

### Gradual Changes

1. Copy a core module: `cp core/anti-laziness.md core/anti-laziness-relaxed.md`
2. Modify the copy
3. A/B test both versions
4. Keep the winner

### Per-Agent Overrides

```markdown
<!-- In specific agent file -->

{{include: behavioral-framework/core/anti-laziness.md}}

## Agent-Specific Overrides
- For this agent, allow TODO comments in draft phase
- Require verification only for production code
```

## Testing Your Behavioral Framework

Run the test suite to verify behavior:

```bash
# Test that agents follow anti-laziness rules
python tests/test_behaviors.py --behavior anti-laziness

# Test verification loops work
python tests/test_verification.py --integration mcp-devtools

# Full behavioral test suite
python tests/run_all_tests.py
```

## Monitoring Behavior Compliance

Use the observability system to track:

- Are agents verifying before claiming success?
- Are errors being reported first?
- Are tests being run?

```bash
# Check compliance metrics
python monitoring/check_compliance.py --agent local-coder --period 24h
```

## Version Control Strategy

Track what works:

```bash
# Tag working configurations
git tag -a behavior-v1.0 -m "Paranoid verification, works great"

# Branch for experiments
git checkout -b experiment/relaxed-verification

# Compare behavior versions
python tools/compare_behaviors.py v1.0 v1.1
```

## Best Practices

1. **Start Strict, Relax Later**: Begin with paranoid verification, then relax as needed
2. **One Change at a Time**: Modify one behavior module at a time to isolate effects
3. **Monitor Metrics**: Use observability to measure behavior compliance
4. **Document Deviations**: If you override a rule, document why
5. **Test Behaviors**: Write tests for behavioral patterns, not just code

## Troubleshooting

**Agent is too verbose?**
→ Set `communication_style: "balanced"` in config

**Agent still being lazy?**
→ Increase `verification_strictness: "paranoid"`

**Agent not using MCP tools?**
→ Check `integrations/mcp-devtools.md` is included

**False positives in verification?**
→ Adjust `verification-requirements.json` thresholds

## Contributing

When adding new behavioral patterns:

1. Create module in `core/` or `integrations/`
2. Document in this README
3. Add config options to relevant JSON files
4. Create tests in `tests/`
5. Update composer to support new module

## License

MIT - Use freely, modify as needed
