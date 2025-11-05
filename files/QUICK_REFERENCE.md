# Quick Reference Card

## Essential Commands

### Create an Agent

```bash
# Paranoid production agent (maximum safety)
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops,error-first-communication \
  --integrations mcp-devtools \
  --output agents/paranoid-coder.md

# Balanced development agent
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops \
  --output agents/dev-agent.md

# Fast prototype agent
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,error-first-communication \
  --config-override '{"active_preset":"relaxed_prototype"}' \
  --output agents/prototype-agent.md
```

### List Available Modules

```bash
# List all behavioral modules
python composer/agent-composer.py --list-behaviors

# List all integration modules
python composer/agent-composer.py --list-integrations
```

### Adjust Configuration

Edit `config/behavior-settings.json`:

```json
{
  "anti_laziness": {
    "strictness": "paranoid"  // paranoid, normal, relaxed
  },
  "verification_loops": {
    "minimum_verification_layers": 2
  }
}
```

---

## Key File Locations

```
behavioral-framework/
├── core/                    # Core behavioral patterns
│   ├── anti-laziness.md
│   ├── humility-protocol.md
│   ├── verification-loops.md
│   └── error-first-communication.md
│
├── integrations/            # Tool-specific behaviors
│   └── mcp-devtools.md
│
├── templates/               # Agent templates
│   └── local-coder-agent.md
│
├── config/                  # Configuration
│   └── behavior-settings.json
│
└── composer/                # Build system
    └── agent-composer.py
```

---

## Common Patterns

### Pattern 1: Different Agents for Different Tasks

```bash
# Local coder for standard work
qwen2.5-coder:14b + anti-laziness + verification

# Cloud reasoner for complex decisions
claude-sonnet-4 + humility-protocol + error-first

# UI specialist for frontend
qwen2.5-coder:14b + all modules + mcp-devtools
```

### Pattern 2: Strictness by Environment

```bash
# Development: Balanced
--config-override '{"active_preset":"balanced_development"}'

# Staging: Stricter
--config-override '{"active_preset":"paranoid_production"}'

# Production: Paranoid
--config-override '{"active_preset":"paranoid_production"}'
```

### Pattern 3: A/B Testing

```bash
# Version A: Strict verification
python composer/agent-composer.py \
  --behaviors anti-laziness,verification-loops \
  --config-override '{"verification_loops":{"strictness":"paranoid"}}' \
  --output agents/agent-a.md

# Version B: Normal verification
python composer/agent-composer.py \
  --behaviors anti-laziness,verification-loops \
  --config-override '{"verification_loops":{"strictness":"normal"}}' \
  --output agents/agent-b.md

# Test both on same task, compare results
```

---

## Behavioral Modules Quick Reference

| Module | Prevents | Key Rule |
|--------|----------|----------|
| `anti-laziness` | TODO comments, partial work | Complete implementations only |
| `humility-protocol` | Overconfidence | Evidence before claims |
| `verification-loops` | Untested code | Verify everything |
| `error-first-communication` | Hidden errors | Errors at top always |
| `mcp-devtools` | Unverified UI | Browser testing required |

---

## Strictness Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Paranoid** | Zero tolerance | Production code |
| **Normal** | Balanced | Development |
| **Relaxed** | Fast iteration | Prototypes |

---

## Configuration Quick Settings

### Make Agent Less Verbose

```json
{
  "verification_loops": {
    "show_verification_evidence": "summary"  // vs "always"
  }
}
```

### Make Agent More Paranoid

```json
{
  "anti_laziness": {
    "strictness": "paranoid",
    "minimum_implementation_percentage": 100
  }
}
```

### Require Browser Testing

```json
{
  "mcp_devtools": {
    "require_for_ui": true,
    "check_console": true
  }
}
```

---

## Integration with OpenCode

### 1. Copy framework to OpenCode

```bash
cp -r behavioral-framework /path/to/opencode/.agents/
```

### 2. Create agents

```bash
cd /path/to/opencode/.agents/behavioral-framework
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops \
  --output ../agents/local-coder.md
```

### 3. Configure OpenCode

Edit `.opencode/config.json`:

```json
{
  "agents": {
    "local-coder": {
      "model": "qwen2.5-coder:14b",
      "system_prompt_file": ".agents/agents/local-coder.md"
    }
  }
}
```

---

## Observability Setup

### Start Observability Server

```bash
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh

# Visit http://localhost:5173
```

### Send Events from OpenCode

```go
// In your agent code
observability.SendEvent("AgentCompleted", map[string]interface{}{
    "agent": "local-coder",
    "task": taskID,
    "verified": true,
})
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent too verbose | Set `"show_verification_evidence": "summary"` |
| Agent being lazy | Increase `strictness` to `"paranoid"` |
| Agent not using MCP | Include `--integrations mcp-devtools` |
| False positives | Adjust `verification_requirements` in config |

---

## Hardware Reference (Your Setup)

```
HP Z440 Workstation
├── RAM: 64 GB (can run 70B models in low quant)
├── GPU: NVIDIA 3060 12GB
│   ├── Optimal: Qwen 2.5 Coder 14B Q5_K_M (~9GB VRAM)
│   ├── Alternative: Qwen 2.5 Coder 7B Q8_0 (~8GB VRAM)
│   └── Fallback: DeepSeek Coder 6.7B (~7GB VRAM)
└── Ollama: Recommended for local model management
```

### Pull Optimal Model

```bash
ollama pull qwen2.5-coder:14b-instruct-q5_K_M
```

---

## Quick Test

### Test Your Framework Works

```bash
# 1. Create test agent
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,verification-loops \
  --output test-agent.md

# 2. Check output contains:
grep "TODO" test-agent.md  # Should say "FORBIDDEN"
grep "Verification" test-agent.md  # Should have verification rules

# 3. Success if both found ✓
```

---

## Resources

- **Full Documentation**: [README.md](behavioral-framework/README.md)
- **Usage Guide**: [QUICKSTART.md](behavioral-framework/QUICKSTART.md)
- **Integration**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Overview**: [SUMMARY.md](SUMMARY.md)

---

## Support & Updates

- GitHub Issues: For bugs and feature requests
- Version Control: Tag working configurations
- A/B Testing: Test changes before applying globally
- Monitoring: Use observability to track compliance

---

**Remember:** The framework is modular. Start with what you need, expand as you grow.

🚀 Happy building!
