# Complete Integration Guide: Multi-Agent Orchestrator with Behavioral Framework

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              MAIN ORCHESTRATOR (Claude/Gemini)                   │
│         Built on OpenCode + Custom Orchestration Layer           │
│         Uses: behavioral-framework for all agents                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  TASK ROUTER    │
                    │  (Orchestrator) │
                    └─────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                      ↓
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│ LOCAL AGENT    │   │ CLOUD AGENT    │   │ SPECIALIZED    │
│ (Qwen 14B)     │   │ (Claude CLI)   │   │ AGENT          │
│ + behavioral-  │   │ + behavioral-  │   │ + behavioral-  │
│ framework      │   │ framework      │   │ framework      │
└────────────────┘   └────────────────┘   └────────────────┘
        ↓                     ↓                      ↓
        └─────────────────────┼─────────────────────┘
                              ↓
        ══════════════════════════════════════════════════
                     OBSERVABILITY LAYER
               (claude-code-hooks-multi-agent)
                 Monitors ALL agents in real-time
        ══════════════════════════════════════════════════
```

---

## The Complete Stack

### 1. OpenCode (Base Platform)
- Multi-provider support
- MCP integration
- Client/server architecture
- Tool system

**Your modification:** Add orchestrator layer

### 2. Behavioral Framework (Agent Quality Control)
- Modular behavioral patterns
- Prevents laziness, overconfidence
- Enforces verification
- Error-first communication

**Your creation:** This modular system we just built

### 3. Observability System (Monitoring)
- Real-time event tracking
- Multi-agent session management
- WebSocket streaming
- SQLite storage

**From:** claude-code-hooks-multi-agent-observability

---

## Integration Steps

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Set Up OpenCode

```bash
# Clone OpenCode
git clone https://github.com/sst/opencode.git
cd opencode

# Create orchestrator branch
git checkout -b multi-agent-orchestrator

# Build
go build -o opencode
```

#### 1.2 Set Up Behavioral Framework

```bash
# Copy behavioral framework into OpenCode
cp -r /path/to/behavioral-framework opencode/.agents/
```

#### 1.3 Set Up Observability

```bash
# Clone observability system
git clone https://github.com/disler/claude-code-hooks-multi-agent-observability.git
cd claude-code-hooks-multi-agent-observability

# Start server
./scripts/start-system.sh

# Visit http://localhost:5173 to see dashboard
```

#### 1.4 Set Up Local Model

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen 2.5 Coder 14B
ollama pull qwen2.5-coder:14b-instruct-q5_K_M

# Test it
ollama run qwen2.5-coder:14b-instruct-q5_K_M
```

---

### Phase 2: Create Agents (Week 2)

#### 2.1 Create Local Coder Agent

```bash
cd opencode/.agents/behavioral-framework

# Create paranoid local coder
python composer/agent-composer.py \
  --template templates/local-coder-agent.md \
  --behaviors anti-laziness,humility-protocol,verification-loops,error-first-communication \
  --integrations mcp-devtools \
  --output ../agents/local-coder.md
```

#### 2.2 Create Cloud Reasoner Agent

Create `templates/cloud-reasoner-agent.md`:

```markdown
# Cloud Reasoner Agent

**Model:** Claude Sonnet 4 / Gemini 2.5 Pro  
**Purpose:** Complex reasoning, architecture decisions

[Similar structure to local-coder-agent]
```

Then compose:

```bash
python composer/agent-composer.py \
  --template templates/cloud-reasoner-agent.md \
  --behaviors humility-protocol,error-first-communication \
  --output ../agents/cloud-reasoner.md
```

#### 2.3 Configure OpenCode to Use Agents

Edit `opencode/.opencode/config.json`:

```json
{
  "agents": {
    "local-coder": {
      "model": "qwen2.5-coder:14b-instruct",
      "provider": "ollama",
      "system_prompt_file": ".agents/agents/local-coder.md",
      "max_tokens": 4000
    },
    "cloud-reasoner": {
      "model": "claude-sonnet-4",
      "provider": "anthropic",
      "system_prompt_file": ".agents/agents/cloud-reasoner.md",
      "max_tokens": 8000
    }
  }
}
```

---

### Phase 3: Build Orchestrator (Week 3)

#### 3.1 Create Orchestrator Module

Create `opencode/internal/orchestrator/coordinator.go`:

```go
package orchestrator

import (
    "github.com/opencode-ai/opencode/internal/llm"
    "github.com/opencode-ai/opencode/internal/observability"
)

type Coordinator struct {
    agents          map[string]*Agent
    observability   *observability.Client
    taskDecomposer  *TaskDecomposer
    router          *AgentRouter
}

type Agent struct {
    Name     string
    Model    string
    Provider string
    Prompt   string
}

type Task struct {
    ID          string
    Description string
    Type        string  // "code", "reasoning", "testing", etc.
    Priority    int
    Dependencies []string
}

func NewCoordinator(config Config) *Coordinator {
    return &Coordinator{
        agents:        loadAgents(config),
        observability: observability.NewClient("http://localhost:4000"),
        taskDecomposer: NewTaskDecomposer(),
        router:        NewAgentRouter(),
    }
}

func (c *Coordinator) HandleRequest(prompt string) (*Response, error) {
    // 1. Send TaskDecomposed event
    c.observability.SendEvent("TaskDecomposed", map[string]interface{}{
        "prompt": prompt,
        "timestamp": time.Now(),
    })
    
    // 2. Decompose into sub-tasks
    tasks := c.taskDecomposer.Decompose(prompt)
    
    // 3. Route tasks to appropriate agents
    results := make(chan *TaskResult, len(tasks))
    
    for _, task := range tasks {
        agent := c.router.SelectAgent(task)
        
        c.observability.SendEvent("AgentRouted", map[string]interface{}{
            "task": task.ID,
            "agent": agent.Name,
        })
        
        go c.executeTask(agent, task, results)
    }
    
    // 4. Collect and aggregate results
    return c.aggregateResults(results, len(tasks))
}

func (c *Coordinator) executeTask(agent *Agent, task *Task, results chan *TaskResult) {
    c.observability.SendEvent("AgentSpawned", map[string]interface{}{
        "agent": agent.Name,
        "task": task.ID,
    })
    
    // Execute task with agent
    result := agent.Execute(task)
    
    c.observability.SendEvent("AgentCompleted", map[string]interface{}{
        "agent": agent.Name,
        "task": task.ID,
        "success": result.Success,
    })
    
    results <- result
}
```

#### 3.2 Create Task Decomposer

Create `opencode/internal/orchestrator/decomposer.go`:

```go
package orchestrator

type TaskDecomposer struct {
    llm LLMClient
}

func (td *TaskDecomposer) Decompose(prompt string) []Task {
    // Use Claude/Gemini to decompose task
    systemPrompt := `You are a task decomposition specialist.
    
Break this request into atomic, independent sub-tasks.

For each task, specify:
- Type: "code", "reasoning", "testing", "research"
- Description: What needs to be done
- Dependencies: Which other tasks must complete first

Return JSON array of tasks.`

    response := td.llm.Complete(systemPrompt, prompt)
    
    // Parse JSON response into tasks
    var tasks []Task
    json.Unmarshal([]byte(response), &tasks)
    
    return tasks
}
```

#### 3.3 Create Agent Router

Create `opencode/internal/orchestrator/router.go`:

```go
package orchestrator

type AgentRouter struct {
    agents map[string]*Agent
}

func (ar *AgentRouter) SelectAgent(task *Task) *Agent {
    switch task.Type {
    case "code":
        // Simple CRUD, data processing → Local Agent
        if task.Complexity() < 5 {
            return ar.agents["local-coder"]
        }
        // Complex architecture → Cloud Agent
        return ar.agents["cloud-reasoner"]
        
    case "reasoning":
        return ar.agents["cloud-reasoner"]
        
    case "testing":
        return ar.agents["test-agent"]
        
    case "research":
        return ar.agents["research-agent"]
        
    default:
        return ar.agents["local-coder"]
    }
}
```

---

### Phase 4: Connect Observability (Week 4)

#### 4.1 Create OpenCode → Observability Adapter

Create `opencode/internal/observability/client.go`:

```go
package observability

import (
    "bytes"
    "encoding/json"
    "net/http"
    "time"
)

type Client struct {
    serverURL string
    sourceApp string
}

type Event struct {
    SourceApp     string                 `json:"source_app"`
    SessionID     string                 `json:"session_id"`
    HookEventType string                 `json:"hook_event_type"`
    Payload       map[string]interface{} `json:"payload"`
    Timestamp     string                 `json:"timestamp"`
}

func NewClient(serverURL string) *Client {
    return &Client{
        serverURL: serverURL,
        sourceApp: "opencode-orchestrator",
    }
}

func (c *Client) SendEvent(eventType string, payload map[string]interface{}) error {
    event := Event{
        SourceApp:     c.sourceApp,
        SessionID:     getCurrentSessionID(),
        HookEventType: eventType,
        Payload:       payload,
        Timestamp:     time.Now().Format(time.RFC3339),
    }
    
    jsonData, err := json.Marshal(event)
    if err != nil {
        return err
    }
    
    _, err = http.Post(
        c.serverURL+"/events",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    return err
}
```

#### 4.2 Add Custom Event Types

Edit `claude-code-hooks-multi-agent-observability/apps/server/src/types.ts`:

```typescript
export type EventType = 
  // Existing types
  | "PreToolUse"
  | "PostToolUse"
  // ... other existing types
  
  // NEW: Multi-agent orchestration events
  | "TaskDecomposed"
  | "AgentSpawned"
  | "AgentRouted"
  | "AgentCompleted"
  | "ResultAggregated"
  | "CostCalculated"
  | "ModelSwitched"
  | "LocalModelInvoked"
  | "CloudModelInvoked";
```

---

## Complete Usage Example

### Scenario: User asks to build a full-stack TODO app

```
User: "Create a full-stack TODO app with React frontend and Node.js backend"

↓

Orchestrator receives request
  ├─ Sends "TaskDecomposed" event to observability
  ├─ Breaks into tasks:
  │   1. Design API structure (reasoning)
  │   2. Create backend endpoints (code)
  │   3. Create React components (code + UI verification)
  │   4. Write tests (testing)
  │   5. Deploy (deployment)
  │
  ├─ Routes tasks:
  │   ├─ Task 1 → Cloud Reasoner (architectural decision)
  │   ├─ Task 2 → Local Coder (standard CRUD)
  │   ├─ Task 3 → Local Coder + MCP DevTools (UI work)
  │   ├─ Task 4 → Test Agent (testing)
  │   └─ Task 5 → Cloud Reasoner (deployment strategy)
  │
  └─ Each agent:
      ├─ Follows behavioral framework (no TODOs, verify everything)
      ├─ Sends events to observability
      └─ Returns complete, tested results

↓

Orchestrator aggregates results
  ├─ Sends "ResultAggregated" event
  └─ Returns complete TODO app to user

↓

User sees:
  ├─ Real-time progress in observability dashboard
  ├─ Which agents worked on what
  ├─ All verification steps
  └─ Complete, working application
```

---

## Monitoring & Debugging

### View Real-Time Activity

```
Open http://localhost:5173

You'll see:
- TaskDecomposed events (orchestrator planning)
- AgentRouted events (task assignments)
- AgentSpawned events (agents starting work)
- PreToolUse/PostToolUse events (agent actions)
- AgentCompleted events (agents finishing)
- ResultAggregated events (final assembly)

Filter by:
- Agent name (local-coder, cloud-reasoner, etc.)
- Session ID
- Event type
```

### Debug Agent Behavior

```
1. Check if agent is verifying:
   - Look for "Testing", "Verifying" in agent output
   - Look for command executions and outputs
   
2. Check if agent is being lazy:
   - Search for "TODO" in code (should be 0)
   - Check implementation completeness
   
3. Check if errors are reported first:
   - Look at agent output structure
   - Errors should be at top with 🚨 emoji
```

---

## Next Steps

1. ✅ Clone all three repos (OpenCode, behavioral-framework, observability)
2. ✅ Set up local model (Qwen 14B on your 3060)
3. ✅ Create your first agents using composer
4. ✅ Build orchestrator layer in OpenCode
5. ✅ Connect observability
6. ✅ Test with simple multi-agent task
7. ✅ Iterate and improve!

---

## Your Competitive Advantage

You now have:
1. **Multi-provider flexibility** (not locked to one AI)
2. **Cost optimization** (local for simple, cloud for complex)
3. **Behavioral engineering** (agents that don't lie)
4. **Real-time observability** (see everything happening)
5. **Full control** (modify any part of the system)

This is Claude Code++. 🚀
