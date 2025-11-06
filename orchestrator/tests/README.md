# Rozet Orchestrator Test Suite

## Quick Start

### Run Unit Tests (Fast, No API Calls)

```bash
cd /Users/urirozen/projects/rozet
source .venv/bin/activate
pytest orchestrator/tests/unit/ -v
```

### Run Integration Tests (Real API Calls, Costs Money)

```bash
export ORCHESTRATOR_USE_REAL_API=true
export OPENAI_API_KEY="your-key-here"
pytest orchestrator/tests/integration/ -v -s
```

### Run Specific Test

```bash
# Unit test
pytest orchestrator/tests/unit/test_config_loader.py::test_load_valid_config -v

# Integration test
export ORCHESTRATOR_USE_REAL_API=true
pytest orchestrator/tests/integration/test_codebase_summary.py::test_summarize_orchestrator_codebase -v -s
```

## Test Structure

- **unit/**: Fast tests, no API calls, test individual components
- **integration/**: Real API calls, test components working together
- **e2e/**: Full user workflows (coming soon)

## Writing New Tests

### Unit Test Example

```python
def test_my_component():
    """Test my component in isolation."""
    component = MyComponent()
    result = component.do_something()
    assert result == expected_value
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run",
)
def test_real_scenario(api_key: str):
    """Test with real API calls."""
    orchestrator = setup_orchestrator()
    result = orchestrator.handle_request("real request")
    assert result is not None
```

## Test Philosophy

- ✅ **Real scenarios**: Test with actual use cases
- ✅ **Real tools**: Use real file operations, bash commands
- ✅ **Real LLM calls**: Use GPT-5-nano for integration tests
- ✅ **Verify outcomes**: Check actual results, not just that code ran

## Cost Management

Integration tests use real API calls. To minimize costs:

1. Use GPT-5-nano (cheapest model)
2. Run integration tests selectively
3. Use `--use-real-api` flag to control when real APIs are used
4. Mock expensive operations in unit tests

