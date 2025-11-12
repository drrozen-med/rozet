# OpenCode Provider/Model System Fix - Build Plan

**Priority:** CRITICAL - Model switching and provider control  
**Status:** ✅ **COMPLETED** - All 5 steps implemented and tested (31 tests passing)  
**Last Updated:** 2025-01-27  
**See:** `OPENCODE_PROVIDER_FIX_SUMMARY.md` for implementation details

## 🎯 Objective

Fix OpenCode's model switching and provider system to provide **precise, programmatic control** over model/provider selection, configuration, and switching. Replace OpenCode's complex, hardcoded system with our clean, configurable orchestrator approach.

## 🔍 Current Problems with OpenCode's System

### Issues Identified

1. **Hardcoded Priorities** (`provider.ts:619-626`)
   - Fixed priority list: `["gemini-2.5-pro-preview", "gpt-5", "claude-sonnet-4"]`
   - No way to override or customize
   - `getSmallModel()` has hardcoded priority list

2. **Complex State Management** (`provider.ts:233-471`)
   - Multiple sources (env, config, custom, api) with unclear precedence
   - State is cached in `Instance.state()` - hard to test/reset
   - Provider loading happens in complex merge logic

3. **Model Filtering/Blacklisting** (`provider.ts:440-454`)
   - Hardcoded blacklist: `gpt-5-chat-latest`
   - Experimental model filtering tied to flags
   - No programmatic way to override

4. **Default Model Selection** (`provider.ts:629-679`)
   - Reads from TUI state file (hardcoded path)
   - Falls back to sorted models (uses hardcoded priority)
   - No clean API for programmatic selection

5. **Provider Loading Logic** (`provider.ts:285-432`)
   - Multiple merge points (env → api → custom → config)
   - Unclear precedence when conflicts occur
   - Custom loaders are provider-specific, not general

6. **No Testing Infrastructure**
   - State is global singleton
   - Hard to mock/test different configurations
   - No programmatic API for testing

## ✅ Our Orchestrator's Superior Approach

### What We Have (That Works)

1. **Clean Config System** (`config/providers.yaml`)
   - YAML-based, human-readable
   - Clear provider/model mapping
   - Environment variable overrides

2. **Simple Factory Pattern** (`orchestrator/providers/factory.py`)
   - One function: `create_chat_model(config)`
   - Returns LangChain model directly
   - No complex state management

3. **Environment Overrides** (`orchestrator/config_loader.py`)
   - `ROZET_ORCHESTRATOR_PROVIDER=ollama`
   - `ROZET_ORCHESTRATOR_MODEL=gpt-oss:20b`
   - Simple, predictable precedence

4. **Testable** (`orchestrator/tests/unit/test_provider_factory.py`)
   - Unit tests for each provider
   - Mockable, no global state
   - Clear test cases

## 📋 Build Plan - Phase 1: Provider System Fix

### Step 1: Create OpenCode Provider Bridge (Python)

**Goal:** Create a Python module that wraps OpenCode's provider system with our clean interface.

**Files to Create:**
- `orchestrator/integrations/opencode_provider_bridge.py`
- `orchestrator/integrations/opencode_provider_config.py`

**Implementation:**
```python
# opencode_provider_bridge.py
class OpenCodeProviderBridge:
    """Bridge between OpenCode's provider system and our clean interface."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with our config system."""
        self.config = load_provider_config(config_path)
    
    async def get_model(self, provider_id: str, model_id: str) -> LanguageModel:
        """Get model via OpenCode SDK with our config."""
        # Use OpenCode Python SDK
        # Apply our config overrides
        # Return LangChain-compatible model
    
    def list_providers(self) -> List[str]:
        """List available providers (from our config + OpenCode)."""
    
    def list_models(self, provider_id: str) -> List[str]:
        """List available models for provider."""
```

**Tests:**
- `orchestrator/tests/integration/test_opencode_provider_bridge.py`
- Test model switching
- Test provider selection
- Test config overrides

**Success Criteria:**
- ✅ Can programmatically switch models
- ✅ Config-driven (not hardcoded)
- ✅ Testable with existing test infrastructure
- ✅ Works with OpenCode SDK

### Step 2: Replace OpenCode's Default Model Selection

**Goal:** Override OpenCode's hardcoded default model logic.

**Approach:**
- Create OpenCode command/plugin that uses our provider bridge
- Override `Provider.defaultModel()` behavior
- Use our config as source of truth

**Files to Modify:**
- `opencode/packages/opencode/src/provider/provider.ts` (or create wrapper)
- `orchestrator/integrations/opencode_provider_override.ts` (new)

**Implementation:**
```typescript
// opencode_provider_override.ts
export async function getDefaultModel(): Promise<{providerID: string, modelID: string}> {
  // Read from our config/providers.yaml
  // Parse via Python bridge or direct YAML read
  // Return our configured default
}
```

**Tests:**
- Test default model selection from config
- Test fallback behavior
- Test environment overrides

**Success Criteria:**
- ✅ Default model comes from our config
- ✅ No hardcoded priorities
- ✅ Environment overrides work

### Step 3: Fix Model Filtering/Blacklisting

**Goal:** Make model filtering configurable, not hardcoded.

**Approach:**
- Add `disabled_models` to our config
- Add `allowed_models` to our config
- Filter OpenCode's model list through our config

**Files to Modify:**
- `config/providers.yaml` (add filtering options)
- `orchestrator/integrations/opencode_provider_bridge.py` (add filtering)

**Config Example:**
```yaml
# config/providers.yaml
opencode:
  disabled_models:
    - "gpt-5-chat-latest"  # Override OpenCode's hardcoded blacklist
  allowed_models_only: false  # If true, only show allowed_models
  allowed_models:
    - "openai/gpt-5-nano"
    - "anthropic/claude-3-5-sonnet"
```

**Tests:**
- Test model filtering
- Test blacklist override
- Test whitelist mode

**Success Criteria:**
- ✅ Configurable model filtering
- ✅ Can override OpenCode's blacklist
- ✅ Can whitelist specific models

### Step 4: Fix Provider Loading Precedence

**Goal:** Make provider loading order clear and configurable.

**Approach:**
- Document precedence: Config → Env → OpenCode Defaults
- Add `provider_priority` to config
- Override OpenCode's merge logic

**Config Example:**
```yaml
# config/providers.yaml
provider_priority:
  - "openrouter"  # Try first
  - "openai"      # Fallback
  - "anthropic"   # Last resort
```

**Tests:**
- Test provider precedence
- Test config override
- Test fallback behavior

**Success Criteria:**
- ✅ Clear precedence order
- ✅ Configurable priority
- ✅ Predictable behavior

### Step 5: Create Programmatic API

**Goal:** Expose clean API for model/provider operations.

**Files to Create:**
- `orchestrator/integrations/opencode_provider_api.py`

**API:**
```python
class OpenCodeProviderAPI:
    """Clean API for OpenCode provider/model operations."""
    
    def switch_model(self, provider_id: str, model_id: str) -> bool:
        """Switch to specific model. Returns success."""
    
    def get_current_model(self) -> Tuple[str, str]:
        """Get current provider/model."""
    
    def list_available_models(self, provider_id: Optional[str] = None) -> List[Dict]:
        """List available models with metadata."""
    
    def validate_model(self, provider_id: str, model_id: str) -> bool:
        """Validate model is available and configured."""
```

**Tests:**
- `orchestrator/tests/integration/test_opencode_provider_api.py`
- Test all API methods
- Test error handling
- Test concurrent access

**Success Criteria:**
- ✅ Clean, simple API
- ✅ All operations testable
- ✅ Error handling works

## 🧪 Testing Strategy

### Use Existing Test Infrastructure

**Test Files:**
- `orchestrator/tests/integration/test_opencode_provider_bridge.py`
- `orchestrator/tests/integration/test_opencode_provider_api.py`
- `orchestrator/tests/unit/test_opencode_provider_config.py`

**Test Approach:**
1. **Unit Tests:** Test config parsing, model creation
2. **Integration Tests:** Test with OpenCode SDK (mocked or real)
3. **E2E Tests:** Test full model switching workflow

**Test Commands:**
```bash
# Run provider tests
pytest orchestrator/tests/integration/test_opencode_provider* -v

# Run all tests
python scripts/test_rozet.py
```

### Test Scenarios

1. **Model Switching**
   - Switch from OpenAI to Anthropic
   - Switch from cloud to local (Ollama)
   - Switch with invalid model (should fail gracefully)

2. **Config Overrides**
   - Environment variable overrides config
   - Config overrides OpenCode defaults
   - Multiple override sources (test precedence)

3. **Provider Loading**
   - Provider with API key works
   - Provider without API key is skipped
   - Custom provider configuration

4. **Model Filtering**
   - Blacklisted models are hidden
   - Whitelisted models only mode
   - Experimental models (with/without flag)

## 📊 Success Metrics

### Phase 1 Complete When:

- ✅ Can programmatically switch models via clean API
- ✅ Config-driven (no hardcoded priorities)
- ✅ All operations testable with existing infrastructure
- ✅ Works with OpenCode SDK
- ✅ Environment overrides work
- ✅ Model filtering is configurable
- ✅ Provider precedence is clear

### Quality Gates:

- ✅ All tests passing
- ✅ No hardcoded model priorities
- ✅ Config is source of truth
- ✅ API is simple and testable
- ✅ Documentation complete

## 🚫 Out of Scope (For Now)

- TUI modifications (wait until end)
- OpenCode core provider.ts refactoring (use bridge instead)
- OpenCode model database changes (use our config)

## 📝 Next Steps After Phase 1

1. **Phase 2:** Integrate provider bridge into orchestrator
2. **Phase 3:** Use OpenCode tools via provider bridge
3. **Phase 4:** TUI modifications (if still needed)

---

**Status:** Ready to start Step 1  
**Estimated Time:** 2-3 days for Phase 1  
**Dependencies:** OpenCode Python SDK, existing test infrastructure

