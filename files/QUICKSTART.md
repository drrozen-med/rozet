# Quick Start Guide

## Installation

```bash
# Clone or copy the behavioral-framework directory to your project
cp -r behavioral-framework /your/project/path/
cd /your/project/path/behavioral-framework
```

## Basic Usage

### 1. List Available Modules

```bash
# See all behavioral modules
python composer/agent-composer.py --list-behaviors

# See all integration modules
python composer/agent-composer.py --list-integrations
```

### 2. Create Your First Agent

```bash
# Create a paranoid local coder with all safety features
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops,error-first-communication \
  --integrations mcp-devtools \
  --output ../agents/paranoid-coder.md
```

### 3. Use the Agent in OpenCode

```bash
# Copy to OpenCode agents directory
cp agents/paranoid-coder.md /path/to/opencode/.opencode/agents/

# Or reference in your orchestrator
```

## Common Recipes

### Paranoid Production Agent

Maximum safety for production code:

```bash
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops,error-first-communication \
  --integrations mcp-devtools \
  --config-override '{"active_preset":"paranoid_production"}' \
  --output agents/production-agent.md
```

**Characteristics:**
- Zero TODOs allowed
- 100% verification required
- Every claim needs evidence
- Error-first reporting
- Mandatory browser testing for UI

**Best for:** Production deployments, critical features, customer-facing code

---

### Balanced Development Agent

Good balance for daily development:

```bash
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops \
  --config-override '{"active_preset":"balanced_development"}' \
  --output agents/dev-agent.md
```

**Characteristics:**
- Complete implementations required
- Humble communication
- Standard verification
- Balanced error reporting

**Best for:** Feature development, bug fixes, refactoring

---

### Fast Prototype Agent

Faster iteration for experiments:

```bash
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,error-first-communication \
  --config-override '{"active_preset":"relaxed_prototype"}' \
  --output agents/prototype-agent.md
```

**Characteristics:**
- Complete implementations still required
- Relaxed verification
- Quick iteration
- Critical errors reported

**Best for:** Prototypes, experiments, proof of concepts

---

### Web Development Agent

Specialized for web/UI work:

```bash
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops,error-first-communication \
  --integrations mcp-devtools \
  --config-override '{"mcp_devtools":{"enabled":true,"require_for_ui":true}}' \
  --output agents/web-dev-agent.md
```

**Characteristics:**
- Mandatory browser verification
- Console error checking
- Network request validation
- Screenshot evidence

**Best for:** Frontend development, UI work, API testing

---

## Customization

### Adjust Behavior Strictness

Edit `config/behavior-settings.json`:

```json
{
  "anti_laziness": {
    "strictness": "normal"  // Change from "paranoid"
  }
}
```

### Create Custom Behavior Module

1. Create new file: `core/my-custom-behavior.md`
2. Write behavioral rules following existing module patterns
3. Use in composition:

```bash
python composer/agent-composer.py \
  --behaviors anti-laziness,my-custom-behavior \
  ...
```

### Override Specific Settings

```bash
# Make verification less strict for this one agent
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol \
  --config-override '{"verification_loops":{"strictness":"normal"}}' \
  --output agents/relaxed-agent.md
```

---

## Testing Your Agents

### Manual Testing

1. Create test task file:

```markdown
# test-tasks/simple-function.md

Create a function that:
- Takes a list of numbers
- Returns the sum
- Handles empty list
- Raises error for non-numbers
```

2. Run agent with task
3. Check if agent:
   - ✓ Implements complete function
   - ✓ Tests with multiple scenarios
   - ✓ Shows test outputs
   - ✓ Reports errors first (if any)

### Automated Compliance Checking

Create a test script:

```python
# tests/test_agent_behavior.py

def test_no_todos(agent_output):
    """Agent should not produce TODO comments"""
    assert "TODO" not in agent_output
    assert "FIXME" not in agent_output

def test_verification_present(agent_output):
    """Agent should show verification steps"""
    assert "Testing" in agent_output or "Verifying" in agent_output
    assert "Output:" in agent_output

def test_error_first(agent_output_with_error):
    """Errors should appear at the top"""
    lines = agent_output_with_error.split('\n')
    error_line = next(i for i, line in enumerate(lines) if "ERROR" in line)
    assert error_line < 10  # Error should be in first 10 lines
```

---

## Integration with Observability

Connect your agents to the observability system:

```bash
# 1. Ensure observability server is running
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh

# 2. Configure agent to send events
# Add to your agent's tool usage:

After each tool use:
  - Send event to observability server
  - Track verification status
  - Log behavioral compliance
```

---

## Tips & Best Practices

### Start Strict, Relax Later

Begin with paranoid settings and relax as you gain confidence:

```
Week 1: paranoid_production preset
Week 2: balanced_development preset (if too verbose)
Week 3: Custom mix of modules that work for you
```

### One Module at a Time

When debugging agent behavior:
- Change one module at a time
- Test thoroughly
- Document what works

### Monitor Compliance

Use observability to track:
- Are agents actually verifying? (check for test outputs)
- Are errors being reported first? (check message structure)
- Are TODOs appearing? (should be zero)

### Version Your Configurations

```bash
git tag agent-config-v1.0 -m "Working paranoid config"
git tag agent-config-v1.1 -m "Relaxed verification slightly"
```

### A/B Test Behaviors

Run two agents with different configs on same task:
- Compare outputs
- Measure compliance
- Pick winner

---

## Troubleshooting

### Agent is Too Verbose

**Solution:** Reduce verification strictness:

```json
{
  "verification_loops": {
    "show_verification_evidence": "summary"  // instead of "always"
  }
}
```

### Agent Still Being Lazy

**Solution:** Increase anti-laziness strictness:

```json
{
  "anti_laziness": {
    "strictness": "paranoid",
    "minimum_implementation_percentage": 100
  }
}
```

### Agent Not Using MCP Tools

**Solution:** Check integration is included:

```bash
python composer/agent-composer.py \
  --integrations mcp-devtools \  # ← Make sure this is present
  ...
```

### False Positive Verifications

**Solution:** Add specific verification requirements:

```json
{
  "verification_loops": {
    "verification_requirements": {
      "api_call": ["status_code", "response_body", "response_time"]
    }
  }
}
```

---

## Next Steps

1. ✅ Create your first agent using a recipe above
2. ✅ Test it on a simple task
3. ✅ Adjust configuration based on results
4. ✅ Integrate with observability system
5. ✅ Build your multi-agent orchestrator!

---

## Support

- Issues: Create in your repo's issue tracker
- Improvements: Submit PRs for new behavioral modules
- Questions: Document in wiki

---

**Ready to build agents that don't lie about their work!** 🚀
