# Rozet Orchestrator - Comprehensive Test Plan

## Test Philosophy

**Test with REAL scenarios, REAL tools, REAL LLM calls.**

- ✅ Integration tests use actual GPT-5-nano API calls
- ✅ Tests execute real file operations (read, write, bash)
- ✅ Tests verify actual behavior, not mocks
- ✅ End-to-end tests simulate real user workflows

---

## Test Structure

```
orchestrator/tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_config_loader.py
│   ├── test_task_planner.py
│   └── test_context_manager.py
├── integration/             # Real LLM calls, real tools
│   ├── test_task_planning.py
│   ├── test_context_management.py
│   ├── test_file_operations.py
│   └── test_codebase_analysis.py
├── e2e/                     # Full user workflows
│   ├── test_codebase_summary.py
│   ├── test_simple_app_creation.py
│   └── test_multi_file_refactor.py
└── fixtures/                 # Test data and helpers
    ├── sample_codebase/
    └── test_helpers.py
```

---

## Test Categories

### 1. Unit Tests (Fast, No API Calls)

**Purpose**: Test individual components in isolation

**Examples**:
- Config loading with various YAML structures
- Task parsing from JSON responses
- Context manager message serialization
- File path resolution

**Run**: `pytest orchestrator/tests/unit/ -v`

---

### 2. Integration Tests (Real API Calls, Real Tools)

**Purpose**: Test components working together with real LLM and tools

#### 2.1 Task Planning Integration

**Test**: `test_task_planning.py`

```python
def test_plan_simple_request():
    """Test orchestrator can break down a simple request into tasks."""
    planner = TaskPlanner(llm=create_chat_model(...))
    tasks = planner.plan("Create a Python script that prints hello")
    
    assert len(tasks) >= 1
    assert any("python" in t.description.lower() for t in tasks)
    assert any("print" in t.description.lower() for t in tasks)

def test_plan_multi_file_request():
    """Test orchestrator handles multi-file requests."""
    planner = TaskPlanner(llm=create_chat_model(...))
    tasks = planner.plan("Create a REST API with auth endpoints")
    
    assert len(tasks) >= 2
    # Verify tasks have dependencies
    assert any(t.dependencies for t in tasks)
```

#### 2.2 Context Management Integration

**Test**: `test_context_management.py`

```python
def test_context_summarization():
    """Test context manager summarizes old messages."""
    manager = ConversationContextManager(...)
    
    # Add many messages
    for i in range(20):
        manager.add_message(f"User message {i}", f"AI response {i}")
    
    # Verify recent messages are kept, old ones summarized
    recent = manager.recent_messages
    assert len(recent) < 20  # Some summarized
    assert len(recent) > 0    # But recent kept
```

#### 2.3 File Operations Integration

**Test**: `test_file_operations.py`

```python
def test_read_write_cycle():
    """Test orchestrator can read and write files."""
    # Create test file
    test_file = Path("/tmp/test_orchestrator.txt")
    test_file.write_text("original content")
    
    # Use orchestrator to read and modify
    # (This will use real bash/file tools)
    result = orchestrator.execute("Append 'modified' to /tmp/test_orchestrator.txt")
    
    # Verify file was modified
    content = test_file.read_text()
    assert "modified" in content
    assert "original content" in content
```

---

### 3. End-to-End Tests (Full User Workflows)

**Purpose**: Test complete user scenarios from request to result

#### 3.1 Codebase Summary Test

**Test**: `test_codebase_summary.py`

```python
def test_summarize_current_codebase():
    """REAL TEST: Ask orchestrator to summarize the orchestrator codebase."""
    orchestrator = setup_orchestrator()
    
    request = """
    Analyze the orchestrator codebase and provide:
    1. Main components and their responsibilities
    2. How they interact
    3. Key design decisions
    4. Areas for improvement
    """
    
    result = orchestrator.handle_request(request)
    
    # Verify response contains expected information
    assert "task planner" in result.lower() or "task_planner" in result.lower()
    assert "context manager" in result.lower() or "context_manager" in result.lower()
    assert len(result) > 500  # Substantive response
    
    # Verify orchestrator actually read files
    # (Check observability logs or file access logs)
```

#### 3.2 Simple App Creation Test

**Test**: `test_simple_app_creation.py`

```python
def test_create_todo_app():
    """REAL TEST: Create a simple todo app end-to-end."""
    orchestrator = setup_orchestrator()
    test_dir = Path("/tmp/test_todo_app")
    test_dir.mkdir(exist_ok=True)
    
    request = """
    Create a simple Python todo app with:
    - A Todo class with id, title, completed fields
    - Functions to add, list, and complete todos
    - A main() function that demonstrates usage
    - Save to todo.py
    """
    
    result = orchestrator.handle_request(request, working_dir=test_dir)
    
    # Verify files were created
    todo_file = test_dir / "todo.py"
    assert todo_file.exists()
    
    # Verify file contains expected code
    content = todo_file.read_text()
    assert "class Todo" in content
    assert "def add" in content.lower() or "def add_todo" in content.lower()
    assert "def main" in content.lower()
    
    # Verify code actually runs
    import subprocess
    result = subprocess.run(
        ["python", str(todo_file)],
        capture_output=True,
        text=True,
        cwd=str(test_dir)
    )
    assert result.returncode == 0  # Code runs without errors
```

#### 3.3 Multi-File Refactor Test

**Test**: `test_multi_file_refactor.py`

```python
def test_refactor_across_files():
    """REAL TEST: Refactor code across multiple files."""
    # Setup test codebase
    test_dir = setup_test_codebase()
    
    orchestrator = setup_orchestrator()
    
    request = """
    Refactor the codebase to:
    1. Extract common utilities to utils.py
    2. Update imports in all files
    3. Ensure all files still work together
    """
    
    result = orchestrator.handle_request(request, working_dir=test_dir)
    
    # Verify refactoring happened
    assert (test_dir / "utils.py").exists()
    
    # Verify imports were updated
    for py_file in test_dir.glob("*.py"):
        if py_file.name != "utils.py":
            content = py_file.read_text()
            assert "from utils import" in content or "import utils" in content
    
    # Verify code still works
    # (Run tests or import checks)
```

---

## Real Test Scenarios

### Scenario 1: Codebase Analysis

**Request**: "Summarize the orchestrator codebase structure"

**Expected Behavior**:
1. Orchestrator plans tasks:
   - T1: Read orchestrator/ directory structure
   - T2: Read key files (cli.py, task_planner.py, etc.)
   - T3: Analyze code structure
   - T4: Generate summary
2. Workers execute:
   - Use bash tool to list files
   - Use read tool to read files
   - Use LLM to analyze
3. Results aggregated and presented

**Verification**:
- ✅ Files were actually read (check logs)
- ✅ Summary mentions actual components
- ✅ Summary is accurate and useful

---

### Scenario 2: File Operations

**Request**: "Create a Python script that reads config/providers.yaml and prints the orchestrator model name"

**Expected Behavior**:
1. Plan: Create script, read config, extract model
2. Execute: Write script, run it
3. Verify: Script outputs correct model name

**Verification**:
- ✅ Script file exists
- ✅ Script runs without errors
- ✅ Output matches actual config value

---

### Scenario 3: Multi-Step Task

**Request**: "Create a simple REST API with authentication"

**Expected Behavior**:
1. Plan breaks into:
   - T1: Create auth module
   - T2: Create API endpoints
   - T3: Create main server file
   - T4: Write tests
2. Tasks execute with dependencies
3. Final verification

**Verification**:
- ✅ All files created
- ✅ Dependencies respected (auth before API)
- ✅ Code runs (server starts)
- ✅ Tests pass

---

## Test Execution Strategy

### Development Mode (Fast Feedback)

```bash
# Run unit tests only (fast, no API costs)
pytest orchestrator/tests/unit/ -v

# Run specific integration test
pytest orchestrator/tests/integration/test_task_planning.py -v

# Run with real API (costs money)
pytest orchestrator/tests/integration/ -v --use-real-api
```

### CI/CD Mode (Comprehensive)

```bash
# Run all tests
pytest orchestrator/tests/ -v

# With coverage
pytest orchestrator/tests/ --cov=orchestrator --cov-report=html
```

### Manual Testing Mode

```bash
# Run specific scenario interactively
python orchestrator/tests/e2e/test_codebase_summary.py --interactive

# Run with verbose output
python orchestrator/tests/e2e/test_codebase_summary.py --verbose
```

---

## Test Data & Fixtures

### Sample Codebase Fixture

Create `orchestrator/tests/fixtures/sample_codebase/` with:
- Simple Python project structure
- Multiple files with dependencies
- Test files
- Config files

Use for testing:
- Multi-file operations
- Refactoring scenarios
- Dependency resolution

---

## Test Helpers

### `test_helpers.py`

```python
def setup_orchestrator():
    """Create orchestrator instance for testing."""
    config = load_provider_config("config/providers.yaml")
    llm, system_prompt = create_chat_model(config.orchestrator)
    # ... setup orchestrator
    return orchestrator

def setup_test_directory():
    """Create isolated test directory."""
    test_dir = Path(f"/tmp/orchestrator_test_{uuid4()}")
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

def cleanup_test_directory(test_dir: Path):
    """Clean up test directory."""
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
```

---

## Success Criteria

### For Each Test:

1. **Functionality**: Test verifies actual behavior works
2. **Realism**: Uses real LLM calls, real tools, real files
3. **Isolation**: Tests don't interfere with each other
4. **Reproducibility**: Tests produce same results when run multiple times
5. **Verification**: Tests check actual outcomes, not just that code ran

### For Test Suite:

1. **Coverage**: All major components tested
2. **Speed**: Unit tests run in < 1 second each
3. **Cost**: Integration tests use affordable models (GPT-5-nano)
4. **Reliability**: Tests pass consistently (not flaky)
5. **Maintainability**: Tests are easy to update when code changes

---

## Running Tests

### Prerequisites

```bash
# Install test dependencies
uv pip install pytest pytest-cov pytest-mock

# Set up test environment
export OPENAI_API_KEY="your-key"
export ORCHESTRATOR_TEST_MODE=true
```

### Quick Test Run

```bash
# Unit tests only (fast)
pytest orchestrator/tests/unit/ -v

# One integration test
pytest orchestrator/tests/integration/test_task_planning.py::test_plan_simple_request -v

# Full test suite (costs API credits)
pytest orchestrator/tests/ -v --use-real-api
```

---

## Test Maintenance

### When to Update Tests:

- ✅ When adding new features
- ✅ When fixing bugs (add regression test)
- ✅ When refactoring (update tests to match new structure)
- ✅ When API changes (update test expectations)

### Test Quality Checklist:

- [ ] Test uses real tools/APIs (not just mocks)
- [ ] Test verifies actual outcomes
- [ ] Test is isolated (doesn't depend on other tests)
- [ ] Test cleans up after itself
- [ ] Test has clear success criteria
- [ ] Test name describes what it tests

---

## Next Steps

1. ✅ Create test directory structure
2. ✅ Write test helpers and fixtures
3. ✅ Implement unit tests
4. ✅ Implement integration tests
5. ✅ Implement end-to-end tests
6. ✅ Set up CI/CD test execution
7. ✅ Document test results and coverage

