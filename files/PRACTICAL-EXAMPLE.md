# Practical Example: Using the Framework with Your Multi-Agent Orchestrator

## Your Setup

**Hardware:**
- HP Z440 Workstation
- 64GB RAM
- NVIDIA 3060 (12GB VRAM)
- Can run Qwen 2.5 Coder 14B comfortably

**Goal:**
Multi-agent orchestrator based on OpenCode that:
- Uses local models (Qwen 2.5 Coder 14B)
- Uses cloud models (Claude Code CLI, Gemini)
- Has specialized agents
- Deploys sub-agents
- Has full observability via claude-code-hooks-multi-agent-observability

---

## Step-by-Step Implementation

### Phase 1: Setup Framework (5 minutes)

```bash
# 1. Framework is already at /home/claude/.agent-framework/
# Copy to your project
cp -r /home/claude/.agent-framework /path/to/your/orchestrator/

# 2. Navigate to framework
cd /path/to/your/orchestrator/.agent-framework/

# 3. Make scripts executable
chmod +x scripts/*.py
```

### Phase 2: Generate Agent Prompts (10 minutes)

```bash
# Generate prompts for each agent type in your orchestrator

# 1. Local Coder Agent (Qwen 2.5 Coder 14B)
python scripts/compose-prompt.py \
  --template local-coder-agent \
  --profile strict \
  --output ../agents/local-coder-prompt.md

# 2. Cloud Reasoner Agent (Claude Sonnet 4 via CLI)
# First, let's create this template
# (You'll create cloud-reasoner-agent.md template based on local-coder-agent.md)
python scripts/compose-prompt.py \
  --template cloud-reasoner-agent \
  --profile balanced \
  --output ../agents/cloud-reasoner-prompt.md

# 3. Test Agent (Specialized for QA)
python scripts/compose-prompt.py \
  --template test-agent \
  --profile strict \
  --output ../agents/test-agent-prompt.md

# 4. Research Agent (For documentation/web search)
python scripts/compose-prompt.py \
  --template research-agent \
  --profile balanced \
  --output ../agents/research-agent-prompt.md

# 5. Orchestrator Agent (Coordinates others)
python scripts/compose-prompt.py \
  --template orchestrator \
  --profile balanced \
  --output ../agents/orchestrator-prompt.md
```

### Phase 3: Setup Qwen 2.5 with Behavioral Framework

```bash
# Using Ollama (recommended for easy management)

# 1. Create Modelfile for Qwen with behavioral scaffolding
cat > QwenCareful.Modelfile << 'EOF'
FROM qwen2.5-coder:14b-instruct

# Load the behavioral framework
SYSTEM """
$(cat agents/local-coder-prompt.md)
"""

# Tune parameters for careful behavior
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

# Slightly higher temperature for creativity in problem-solving
# But the behavioral framework keeps it honest
EOF

# 2. Create the model
ollama create qwen-careful -f QwenCareful.Modelfile

# 3. Test it
ollama run qwen-careful "Create a file called test.txt with 'hello world' in it"

# Expected behavior:
# - Should write file
# - Should read it back to verify
# - Should show confirmation
# If it doesn't, adjust intensity in config.yaml
```

### Phase 4: Integrate with OpenCode Fork

Your OpenCode fork structure:
```
opencode/
├── orchestrator/
│   ├── coordinator.go           # Main orchestrator
│   ├── task_decomposer.go      # Breaks tasks into subtasks
│   ├── agent_router.go         # Routes to appropriate agents
│   └── observability.go        # Sends events to monitoring
│
├── agents/
│   ├── local-coder/
│   │   ├── agent.go
│   │   └── system-prompt.md    # ← Generated prompt here
│   │
│   ├── cloud-reasoner/
│   │   ├── agent.go
│   │   └── system-prompt.md
│   │
│   └── test-agent/
│       ├── agent.go
│       └── system-prompt.md
│
└── config.yaml                  # OpenCode config
```

**Integration code example:**

```go
// orchestrator/agent_factory.go
package orchestrator

import (
    "os"
    "path/filepath"
)

type AgentType string

const (
    LocalCoder    AgentType = "local-coder"
    CloudReasoner AgentType = "cloud-reasoner"
    TestAgent     AgentType = "test-agent"
)

func CreateAgent(agentType AgentType) (*Agent, error) {
    // Load behavioral prompt
    promptPath := filepath.Join("agents", string(agentType), "system-prompt.md")
    prompt, err := os.ReadFile(promptPath)
    if err != nil {
        return nil, err
    }
    
    // Configure based on agent type
    var config AgentConfig
    switch agentType {
    case LocalCoder:
        config = AgentConfig{
            Model: "qwen-careful",  // Your Ollama model
            Provider: "ollama",
            SystemPrompt: string(prompt),
            Temperature: 0.7,
        }
    case CloudReasoner:
        config = AgentConfig{
            Model: "claude-sonnet-4",
            Provider: "anthropic",
            SystemPrompt: string(prompt),
            Temperature: 0.8,
        }
    case TestAgent:
        config = AgentConfig{
            Model: "qwen-careful",
            Provider: "ollama",
            SystemPrompt: string(prompt),
            Temperature: 0.6,  // Lower for more deterministic testing
        }
    }
    
    return NewAgent(config)
}
```

### Phase 5: Connect Observability

```go
// orchestrator/observability.go
package orchestrator

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type ObservabilityClient struct {
    serverURL string
}

type Event struct {
    SourceApp     string                 `json:"source_app"`
    SessionID     string                 `json:"session_id"`
    HookEventType string                 `json:"hook_event_type"`
    Payload       map[string]interface{} `json:"payload"`
}

func (o *ObservabilityClient) SendEvent(eventType string, payload map[string]interface{}) error {
    event := Event{
        SourceApp:     "multi-agent-orchestrator",
        SessionID:     getCurrentSessionID(),
        HookEventType: eventType,
        Payload:       payload,
    }
    
    jsonData, _ := json.Marshal(event)
    _, err := http.Post(
        o.serverURL+"/events",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    return err
}

// Example usage in coordinator
func (c *Coordinator) RouteTask(task Task) {
    // Send observability event
    c.observability.SendEvent("AgentRouted", map[string]interface{}{
        "task_id": task.ID,
        "task_type": task.Type,
        "agent": selectedAgent.Name,
        "timestamp": time.Now(),
    })
    
    // Execute task
    result := selectedAgent.Execute(task)
    
    // Send completion event
    c.observability.SendEvent("AgentCompleted", map[string]interface{}{
        "task_id": task.ID,
        "agent": selectedAgent.Name,
        "success": result.Success,
        "output": result.Output,
    })
}
```

### Phase 6: Test the Full System

```bash
# 1. Start observability server
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh
# Opens on http://localhost:5173

# 2. Start your orchestrator
cd /path/to/your/orchestrator
go run main.go

# 3. Test with a simple task
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a simple REST API with user endpoints",
    "requirements": ["CRUD operations", "Input validation", "Error handling"]
  }'

# 4. Watch in observability UI:
# - Task decomposition event
# - Agent routing events
# - Tool usage events (from agents)
# - Verification events (from behavioral framework)
# - Agent completion events
```

### Expected Agent Behavior

**Without Framework:**
```
Orchestrator: "Create a REST API with user endpoints"

Agent (Qwen):
"I've successfully created a complete REST API with all CRUD operations!
The API is production-ready with full error handling."

[Code has bugs, nothing tested, partially working]
```

**With Framework:**
```
Orchestrator: "Create a REST API with user endpoints"

Agent (Qwen):
"Task: Create REST API with user endpoints

Step 1: Creating api.js with Express server
[Writes code]
Reading back to verify...
✅ Confirmed: api.js created (156 lines)

Step 2: Implementing CRUD endpoints
- POST /users (create)
- GET /users (list)  
- GET /users/:id (read)
- PUT /users/:id (update)
- DELETE /users/:id (delete)

Step 3: Testing endpoints
Starting server: node api.js
Server: Listening on port 3000

Testing POST /users:
curl -X POST http://localhost:3000/users -d '{\"name\":\"test\"}'
Output: {\"id\":1,\"name\":\"test\"}
✅ Create endpoint working

Testing GET /users:
curl http://localhost:3000/users
Output: [{\"id\":1,\"name\":\"test\"}]
✅ List endpoint working

[Tests all endpoints...]

Step 4: Error handling verification
Testing invalid input:
curl -X POST http://localhost:3000/users -d '{}'
Output: {\"error\":\"Name required\"}
✅ Validation working

Final Status:
✅ REST API implemented and verified
✅ All CRUD endpoints tested
✅ Error handling validated
✅ Server running on port 3000"
```

---

## Adjusting Based on Behavior

### If Agent Too Verbose

Edit `.agent-framework/config.yaml`:
```yaml
modules:
  verification_loops:
    intensity: balanced  # From strict
  
  paranoid_verification:
    enabled: false  # Disable extra checking
```

Regenerate:
```bash
python scripts/compose-prompt.py \
  --template local-coder-agent \
  --config config.yaml \
  --output agents/local-coder-prompt.md
```

### If Agent Not Careful Enough

```yaml
modules:
  verification_loops:
    intensity: strict
    max_unverified_claims: 0
  
  paranoid_verification:
    enabled: true
    intensity: strict
```

### If Agent Too Slow

```yaml
# Use faster model for simple tasks
# Route complex tasks to careful agent
# Route simple tasks to fast agent

# In your orchestrator:
if task.complexity == "simple":
    agent = fastAgent  # Qwen 7B, lenient profile
else:
    agent = carefulAgent  # Qwen 14B, strict profile
```

---

## Real-World Example: Multi-Agent Task

**User Request:**
"Build a todo app with React frontend and Node.js backend"

**Orchestrator Workflow:**

1. **Task Decomposition:**
```
Main Task: Todo App
├── Subtask 1: Design API (Cloud Reasoner)
├── Subtask 2: Implement Backend (Local Coder)
├── Subtask 3: Create Frontend (Local Coder)
├── Subtask 4: Integration Testing (Test Agent)
└── Subtask 5: Documentation (Research Agent)
```

2. **Agent Execution (with behavioral framework):**

**Cloud Reasoner (Claude):**
```
Task: Design API

Analyzing requirements...
API Design:
- POST /todos (create)
- GET /todos (list)
- PATCH /todos/:id (update status)
- DELETE /todos/:id (delete)

Design document created.
✅ API specification complete
```

**Local Coder (Qwen with framework):**
```
Task: Implement Backend

Step 1: Creating Express server
File: server.js (89 lines)
Reading back to verify...
✅ Confirmed: Server structure correct

Step 2: Implementing endpoints
[Writes code for all endpoints]

Step 3: Testing each endpoint
Testing POST /todos:
[Shows curl output]
✅ Create working

Testing GET /todos:
[Shows curl output]
✅ List working

[Tests all endpoints...]

Status: ✅ Backend complete, all endpoints verified
```

**Test Agent (Qwen with framework):**
```
Task: Integration Testing

Test Suite: API Integration Tests

Running test_create_todo.js:
Output: ✓ should create todo (42ms)

Running test_update_todo.js:
Output: ✗ should update status (failed)
🚨 Error: PATCH returns 404

Analyzing failure...
Issue: Route defined as PUT, not PATCH
Notifying Local Coder agent...

After fix:
Running test_update_todo.js:
Output: ✓ should update status (38ms)

Status:
✅ All 8 integration tests passing
```

3. **Observability Dashboard Shows:**
- Task decomposition: 5 subtasks
- Agent routing: 4 agents active
- Tools used: 47 total (Write: 23, Read: 15, Bash: 9)
- Verifications performed: 38
- Errors found and fixed: 3
- Total time: 4m 23s
- Cost: $0.12 (mostly local, some cloud)

---

## Performance Expectations

**With Your Hardware:**

**Qwen 2.5 Coder 14B (Q5_K_M) on 3060 12GB:**
- Inference: ~15-20 tokens/sec
- With framework overhead: ~12-18 tokens/sec
- Response time: 2-8 seconds (depending on task)
- VRAM usage: ~9GB
- Cost: $0 (local)

**Claude Sonnet 4 (via API):**
- Inference: ~40-60 tokens/sec
- Response time: 1-5 seconds
- Cost: ~$0.003/1K input, ~$0.015/1K output

**Orchestrator Efficiency:**
- Simple task: 1 agent, 30s-2m
- Medium task: 2-3 agents, 2-5m
- Complex task: 4+ agents, 5-15m

---

## Monitoring Agent Behavior

Track these metrics in observability:

1. **Verification Rate**: % of write/edit followed by read
   - Target: >95%

2. **Unverified Claims**: Count of "success" without test
   - Target: 0

3. **Error Report Delay**: Words before first error mention
   - Target: <20 words

4. **Solution Proposals**: Problems with fix proposals
   - Target: 100%

5. **Tool Usage**: Read/Bash for verification
   - Target: High correlation with Write/Edit

---

## Next Actions

1. **Generate all agent prompts** using the framework
2. **Setup Qwen 2.5 Coder 14B** with behavioral scaffolding
3. **Integrate with OpenCode fork** coordinator
4. **Connect observability** system
5. **Test with simple tasks** first
6. **Adjust intensity** based on behavior
7. **Scale to complex tasks**

---

## Quick Reference Commands

```bash
# Generate prompt
python scripts/compose-prompt.py \
  --template [template] \
  --profile [strict|balanced|lenient] \
  --output [output-file]

# Create Ollama model
ollama create [name] -f [Modelfile]

# Test agent behavior
ollama run [name] "[test prompt]"

# Start observability
cd claude-code-hooks-multi-agent-observability
./scripts/start-system.sh

# Validate config
python scripts/compose-prompt.py \
  --config config.yaml \
  --template [template] \
  --validate-only
```

---

## Success Criteria

Your multi-agent orchestrator is working well when:

✅ Agents verify all code before claiming success
✅ Errors reported immediately and prominently  
✅ Agents show actual test output, not assumptions
✅ Solutions proposed for every problem
✅ No premature victory declarations
✅ Observability shows high verification rates
✅ User can trust agent responses
✅ Code actually works as claimed

---

**This is everything you need to make Qwen 2.5 behave like a careful engineer instead of an overconfident chatbot.**

Ready to build? 🚀
