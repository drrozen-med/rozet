# Rozet Development Plan

**Last Updated:** 2025-01-27  
**Architecture Decision:** Integrate Rozet INTO OpenCode (not separate REPL)

---

## 🎯 Core Architecture Decision

**Decision:** Integrate Rozet orchestrator logic INTO OpenCode as a plugin/hook, leveraging OpenCode's existing TUI, session management, and tools.

**Why:**
- OpenCode is well-engineered with TUI, sessions, tools, plugins, MCPs
- Avoid duplicating infrastructure (TUI, session management, tool execution)
- We have full source code - can modify OpenCode as needed
- Best of both worlds: OpenCode's infrastructure + our orchestrator logic

**Architecture:**
```
User → opencode (OpenCode TUI)
  ↓
OpenCode Session (native)
  ↓
Rozet Plugin/Hook (our orchestrator logic)
  ├── Task Planning (our code)
  ├── System Prompt Control (our prompts)
  ├── Model Routing (our config)
  └── Multi-Agent Coordination (our workers)
  ↓
OpenCode Tools (native: read, write, bash)
```

---

## ✅ Current State

### What We Have
- ✅ **Rozet Orchestrator** - Task planning, coordination, workers
- ✅ **LangChain Integration** - Context management, model abstraction
- ✅ **Provider Bridge** - Clean API for model/provider control (31 tests passing)
- ✅ **System Prompts** - Configurable behavioral framework
- ✅ **Standalone REPL** - `rozett --repl` (for testing/fallback)
- ✅ **OpenCode Command** - `opencode orchestrator plan` (thin wrapper)
- ✅ **Environment Automation** - `scripts/rozet_dev_env.sh`, `run.sh`, and `run_opencode_rozet.sh` bootstrap creds + observability automatically
- ✅ **Observability Integration** - `scripts/rozet_observability.sh` for one-command start/stop

### What OpenCode Provides
- ✅ **TUI** - Polished SolidJS-based interface
- ✅ **Session Management** - Message history, context
- ✅ **Tool Execution** - read, write, bash (native)
- ✅ **Plugin System** - Hooks for chat flow, tools, config
- ✅ **MCP Support** - Model Context Protocol integration

---

## 🚀 Integration Roadmap

### Phase 1: OpenCode Plugin Foundation
**Goal:** Create OpenCode plugin that hooks into chat flow

**Tasks:**
1. Create `opencode/packages/plugin/src/rozet.ts`
   - Hook into `"chat.message"` or `"chat.params"`
   - Route messages through our orchestrator
   - Return orchestrated response

2. Integration Layer
   - Bridge OpenCode message format ↔ our orchestrator
   - Map OpenCode tools to worker interface
   - Handle context synchronization

3. Configuration
   - Load our `config/providers.yaml` in plugin
   - Apply system prompts via `"chat.params"` hook
   - Route model selection through our provider bridge

**Deliverables:**
- Working plugin that intercepts OpenCode chat
- Basic task planning integration
- System prompt injection

---

### Phase 2: Tool Integration
**Goal:** Workers execute via OpenCode's native tools

**Tasks:**
1. Tool Routing
   - Map orchestrator tasks to OpenCode tool calls
   - Execute via OpenCode's tool system
   - Aggregate results back to orchestrator

2. Worker Adaptation
   - Update workers to use OpenCode tools (not our ToolExecutor)
   - Maintain worker interface (for backward compatibility)
   - Handle tool results and errors

**Deliverables:**
- Workers can execute via OpenCode tools
- Tool results flow back to orchestrator
- Error handling works end-to-end

---

### Phase 3: Full Integration
**Goal:** Complete integration with session management and context

**Tasks:**
1. Session Bridge
   - Sync OpenCode session ↔ our context manager
   - Maintain conversation history
   - Handle session lifecycle

2. Model/Provider Control
   - Integrate provider bridge into OpenCode's model selection
   - Override OpenCode's hardcoded priorities
   - Apply our config-driven approach

3. Multi-Agent Coordination
   - Route tasks to multiple workers
   - Coordinate via OpenCode session
   - Aggregate results

**Deliverables:**
- Full integration with OpenCode
- All features working through OpenCode TUI
- Standalone REPL still works (fallback)

---

### Phase 4: Polish & Testing
**Goal:** Production-ready integration

**Tasks:**
1. Error Handling
   - Graceful fallbacks
   - Clear error messages
   - Recovery mechanisms

2. Testing
   - Integration tests with OpenCode
   - End-to-end workflows
   - Regression tests

3. Documentation
   - Usage guide
   - Architecture docs
   - Migration guide

**Deliverables:**
- Production-ready integration
- Comprehensive tests
- Complete documentation

---

## 🔄 Development Workflow

### Primary: Use Rozet REPL to Build
**Strategy:** Use `rozett --repl` as primary development interface

**Why:**
- "Eat your own dogfood" - experience UX firsthand
- Find bugs naturally through usage
- Validate system works end-to-end
- Self-improving system

**How:**
```bash
rozett --repl

You: create OpenCode plugin for Rozet integration
You: add tool routing to workers
You: integrate session management
You: add tests for the integration
```

**Escape Hatches:**
- Direct code editing for complex refactoring
- OpenCode TUI for testing integration
- Unit tests for isolated components

### Secondary: OpenCode TUI (After Integration)
Once integrated, use OpenCode TUI as primary interface:
```bash
opencode

# Rozet orchestrator logic runs via plugin
# All features accessible through OpenCode TUI
```

---

## 📋 Current Priorities

### Immediate (Phase 1) ✅ Completed
1. **Create OpenCode Plugin**
   - Hook into chat flow ✓
   - Basic orchestrator integration ✓
   - System prompt injection ✓

2. **Test Integration**
   - Verify plugin loads ✓
   - Test message routing ✓
   - Validate prompt injection ✓

### In Flight (Phase 2-3)
3. **Tool Integration**
   - Route workers to OpenCode tools *(current focus: migrate LocalWorker to OpenCode tool APIs)*
   - Test end-to-end execution *(auto-exec path in place; keeping worker plumbing next)*

4. **Session Management**
   - Sync context ✓
   - Handle lifecycle ✓

### Upcoming (Phase 4)
5. **Polish & Production**
   - Error handling *(continue improving failure surfacing)*
   - Comprehensive testing *(expand automated scripts to cover plugin bridge + observability)*
   - Documentation *(update as new scripts/flows land)*

---

## 🧪 Testing Strategy

### Unit Tests
- Test orchestrator components in isolation
- Mock OpenCode SDK
- Verify logic correctness

### Integration Tests
- Test plugin with OpenCode
- Verify tool execution
- Test session management

### End-to-End Tests
- Full workflows through OpenCode TUI
- Real tool execution
- Multi-agent coordination

### Manual Testing
- Use Rozet REPL to build features
- Test in OpenCode TUI
- Validate UX

---

## 📁 Key Files

### Rozet Core
- `orchestrator/core/task_planner.py` - Task planning
- `orchestrator/core/coordinator.py` - Task coordination
- `orchestrator/workers/local_worker.py` - Worker execution
- `orchestrator/integrations/opencode_provider_bridge.py` - Provider control

### OpenCode Integration
- `opencode/packages/plugin/src/rozet.ts` - **NEW** Plugin entry point
- `opencode/packages/opencode/src/cli/cmd/orchestrator.ts` - Existing command (keep for compatibility)

### Configuration
- `config/providers.yaml` - Model/provider settings
- `prompts/orchestrator.md` - System prompts
- `.env` - API keys

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- ✅ Plugin loads in OpenCode
- ✅ Messages route through orchestrator
- ✅ System prompts inject correctly
- ✅ Basic task planning works

### Phase 2 Complete When:
- ✅ Workers execute via OpenCode tools
- ✅ Tool results flow back correctly
- ✅ Error handling works

### Phase 3 Complete When:
- ✅ Full session management integrated
- ✅ Model/provider control works
- ✅ Multi-agent coordination functional

### Phase 4 Complete When:
- ✅ Production-ready
- ✅ All tests passing
- ✅ Documentation complete

---

## 💡 Development Principles

1. **Use Rozet to Build Rozet** - Primary development through REPL
2. **Integrate, Don't Duplicate** - Leverage OpenCode infrastructure
3. **Test Continuously** - Unit, integration, E2E, manual
4. **Iterate Quickly** - Small changes, frequent validation
5. **Document as You Go** - Keep docs updated

---

## 🚨 Known Issues & Risks

### Current Issues
- ⚠️ OpenRouter 401 (account issue, not code)
- ⚠️ Worker timeouts (needs optimization)
- ⚠️ Tool execution not yet integrated

### Risks
- **Plugin Complexity** - OpenCode plugin system may have limitations
- **Breaking Changes** - OpenCode updates might break integration
- **Performance** - Additional layer might slow things down

### Mitigation
- Keep standalone REPL as fallback
- Comprehensive testing
- Monitor performance
- Stay updated with OpenCode changes

---

## 📝 Notes

- Standalone REPL (`rozett --repl`) remains available for testing/fallback
- OpenCode command (`opencode orchestrator plan`) kept for compatibility
- All Rozet logic remains in Python (orchestrator/)
- OpenCode plugin is thin bridge layer
- Full source code access allows modifications as needed

