# Rozet REPL Integration Plan

## Current State ✅

### 1. LangChain Integration (YES, Comprehensive!)
✅ **Context Management**: Uses `ConversationSummaryBufferMemory`  
✅ **Task Planning**: Uses `BaseChatModel` from LangChain  
✅ **Provider Factory**: Returns LangChain-compatible models  
✅ **All LLM calls**: Go through LangChain abstractions  

**Why LangChain is Great Here:**
- ✅ Unified interface for all providers (OpenAI, Gemini, Ollama, etc.)
- ✅ Memory management built-in (summary buffers)
- ✅ Easy to switch providers without code changes
- ✅ Production-ready abstractions
- ✅ Consistent message format across providers

### 2. Model Switching (Already Supported!)
✅ **Local Models**: Qwen via Ollama (`langchain-ollama`)  
✅ **Cloud Models**: OpenAI, Gemini, Anthropic  
✅ **Config-Driven**: Easy switching via `config/providers.yaml`  
✅ **Custom Endpoints**: Support for OpenAI OSS-20, custom APIs  

### 3. Scaffolding/System Prompts (Already Supported!)
✅ **Configurable**: `system_prompt_path` in config  
✅ **Behavioral Framework**: Ready to integrate  
✅ **Provider-Specific**: Each model can have its own prompt  

## Next Milestone: Rozet REPL Based on OpenCode

### Architecture Plan

```
Rozet REPL (based on OpenCode)
├── Core: OpenCode's session/tool infrastructure
├── REPL: Our conversational interface (orchestrator/tui.py)
├── Orchestrator: Task planning & coordination
├── Workers: Local (Qwen) + Cloud (GPT-5 nano/mini)
└── Scaffolding: Behavioral framework system prompts
```

### Integration Steps

#### Step 1: Rozet Command in OpenCode ✅ (Partially Done)
```bash
opencode rozet repl          # Start REPL
opencode rozet plan "task"   # Quick plan
```

#### Step 2: Use OpenCode's Session System
- **OpenCode has**: Session management, message history, tool execution
- **We need**: Integrate our orchestrator into OpenCode's session flow
- **Benefit**: Get all OpenCode tools (read, write, bash, etc.) for free

#### Step 3: LangChain Integration Points
```python
# Current: Our REPL calls LangChain directly
orchestrator_llm.invoke(messages)

# Future: OpenCode session → Our orchestrator → LangChain → Workers
opencode_session → orchestrator.plan() → langchain_model → workers.execute()
```

#### Step 4: Model Routing
```yaml
# config/providers.yaml
orchestrator:
  provider: openai      # or ollama for local
  model: gpt-4o-mini    # or qwen2.5-coder:14b
  
workers:
  local:
    provider: ollama
    model: qwen2.5-coder:14b-instruct-q5_K_M
  cloud_fast:
    provider: openai
    model: gpt-4o-mini
```

### Current Code Structure

```
orchestrator/
├── cli.py              ✅ CLI entry point
├── tui.py              ✅ REPL implementation  
├── core/
│   ├── context_manager.py    ✅ LangChain memory
│   ├── task_planner.py       ✅ LangChain LLM
│   └── coordinator.py        ✅ Task routing
├── providers/
│   └── factory.py            ✅ LangChain model factory
└── config_loader.py          ✅ Config management
```

### What We Need to Build

1. **OpenCode Integration Module**
   - Wrap OpenCode's session/tool system
   - Route to our orchestrator
   - Maintain REPL interface

2. **Session Bridge**
   - OpenCode session → Our orchestrator context
   - Tool execution → OpenCode tools
   - Message history → LangChain memory

3. **Rozet Command**
   - `opencode rozet repl` - Start REPL
   - Integrate with OpenCode's TUI infrastructure (but keep REPL style)

### Benefits of LangChain Here

✅ **Unified Model Interface**: Switch between Qwen/Ollama/OpenAI/Gemini seamlessly  
✅ **Memory Management**: Automatic context summarization  
✅ **Provider Abstraction**: Write once, works with any provider  
✅ **Tool Integration**: LangChain tools can call OpenCode tools  
✅ **Production Ready**: Battle-tested abstractions  

### Next Steps (UPDATED PRIORITY)

1. ✅ Confirm LangChain usage (DONE - we're using it comprehensively)
2. ✅ Model switching capability (DONE - config-driven in our orchestrator)
3. ✅ System prompt scaffolding (DONE - configurable)
4. 🔥 **CURRENT PRIORITY**: Fix OpenCode's model/provider system (see `OPENCODE_PROVIDER_FIX_PLAN.md`)
   - Create provider bridge with clean API
   - Replace hardcoded priorities with config-driven approach
   - Make model switching programmatically controllable
   - Testable with existing infrastructure
5. 🔄 **Then**: Integrate REPL into OpenCode as "Rozet" command
6. 🔄 **After**: Connect OpenCode session system to our orchestrator
7. 🔄 **Finally**: TUI modifications (if still needed)

## Summary

**YES, we're using LangChain extensively!** ✅
- Context management
- Task planning  
- Model abstraction
- Provider switching

**Model switching works!** ✅
- Config-driven
- Local (Qwen/Ollama) + Cloud (OpenAI/Gemini)
- Easy to add OpenAI OSS-20

**System prompts ready!** ✅
- Configurable per provider
- Behavioral framework ready

**Next: Integrate into OpenCode as "Rozet"** 🔄

