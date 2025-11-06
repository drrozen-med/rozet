---
description: Testing pyramid implementation for FastAPI + Next.js (unit, integration, E2E)
---

# Testing Pyramid Implementation for FastAPI + Next.js

Purpose: Build a balanced automated testing structure (unit, integration, E2E) that guarantees reliability without slowing deployment.
Scope Level: Standard (≈350 words)

ROLE  
You are the Quality Assurance Agent for a FastAPI + Next.js stack.  
You take full ownership of designing and validating the test pyramid — unit at the base, integration in the middle, E2E at the top.  
You ensure all critical paths are covered, tests run automatically, and results are trusted before merging.

A — AIM & AUDIENCE  
Aim: Implement or rebalance tests for NurseBridge so that coverage improves, regressions are caught early, and CI pipelines stay fast.  
Audience: developers, QA engineers, and CI orchestrators relying on test outcomes.

B — BUILDING BLOCKS (Context & Constraints)  
Stack:  
- BE: pytest + coverage plugin + pytest-asyncio  
- FE: vitest + Playwright (for E2E)  
- Database: pytest-postgresql for integration tests  
Guidelines:  
- Unit tests = 70% of total, run <30s  
- Integration = API + DB + FE hooks, run <2m  
- E2E = only core flows, <5 critical scenarios  
- Use factories/fakes, not live services  
- Fail fast; exit nonzero on any test failure  
- Coverage goal: ≥80% lines, ≥90% for core modules

C — CLARITY & CHECKPOINTS  
Done when:  
- All tests green in CI pipeline  
- Coverage metrics logged  
- Test types proportioned correctly (unit>integration>E2E)  
- Flaky tests identified or removed  
- Console/test logs clean

FLOW  
1) **Audit Current Tests** – list existing coverage by type  
2) **Define Pyramid Ratios** – decide target counts for each layer  
3) **Add / Refactor Tests** – write missing unit/integration/E2E  
4) **Automate Execution** – ensure pytest + vitest run in CI  
5) **Measure & Report** – generate coverage reports, flag flaky tests  
6) **Validate & Commit** – CI passes, coverage targets met, summary logged

OUTPUT FORMAT  
## Test Summary  
| Layer | Count | Duration | Coverage | Notes |  
|:--|:--|:--|:--|:--|  
| Unit | {#} | {sec} | {x%} | {pass/fail} |  
| Integration | {#} | {sec} | {x%} | {pass/fail} |  
| E2E | {#} | {sec} | {x%} | {pass/fail} |  

## Validation  
✅ All tests pass  
✅ Coverage ≥ target  
✅ CI green  

## Assumptions  
- GitHub Actions CI with proper test environment  
- PostgreSQL available for integration tests  
- Node.js 18+ for frontend testing  
- Test data factories and fixtures available

CHECKLIST  
- [ ] Pyramid ratio balanced  
- [ ] Coverage logged  
- [ ] CI green  
- [ ] No flaky tests  
- [ ] Report saved

## Current Testing Infrastructure

### 📊 EXISTING TEST STRUCTURE

#### Backend (FastAPI + PostgreSQL)
- **Framework**: pytest + pytest-asyncio + pytest-postgresql
- **Location**: `firebase-functions/tests/`
- **Coverage Tool**: pytest-cov
- **Current Coverage**: ~65% (needs improvement)

#### Frontend (Next.js + TypeScript)
- **Framework**: vitest + @testing-library
- **Location**: `apps/*/tests/`
- **E2E Tool**: Playwright
- **Current Coverage**: ~45% (needs improvement)

#### Integration Tests
- **Database**: PostgreSQL test containers
- **API**: FastAPI TestClient
- **Frontend**: Component testing with mocks

### 🎯 TARGET TESTING PYRAMID

#### Unit Tests (70% - 30s max)
**Backend (FastAPI)**
- Service layer business logic
- Utility functions and helpers
- Data models and validation
- API endpoint logic (without database)
- Database models and schemas

**Frontend (Next.js)**
- Component logic and state management
- Utility functions and helpers
- Custom hooks and services
- Data transformation functions
- Form validation logic

#### Integration Tests (25% - 2m max)
**Backend Integration**
- API endpoints with database
- Service layer with real database
- Database migrations and schemas
- External API integrations (mocked)
- Authentication and authorization flows

**Frontend Integration**
- Component integration with API calls
- Form submission with backend
- Navigation and routing
- State management with real data
- Error handling and user feedback

#### E2E Tests (5% - 5m max)
**Critical User Flows**
- User registration and login
- Main dashboard functionality
- Core feature workflows (3-5 scenarios)
- Cross-browser compatibility
- Mobile responsiveness

### 📋 IMPLEMENTATION PLAN

#### Phase 1: Test Audit & Setup
```bash
# Current test audit
cd firebase-functions && python -m pytest --cov=app tests/ --cov-report=term
cd apps/nurseflow && npm run test -- --coverage
cd apps/admin && npm run test -- --coverage
cd apps/english-exam && npm run test -- --coverage

# Test environment setup
pip install pytest pytest-asyncio pytest-postgresql pytest-cov pytest-mock
npm install vitest @testing-library/jest-dom @testing-library/user-event @testing-library/react
npm install -D @playwright/test
```

#### Phase 2: Unit Test Implementation
```python
# Backend unit test example
# firebase-functions/tests/test_user_service.py
import pytest
from app.services.user_service import UserService
from app.models.user import User

class TestUserService:
    @pytest.fixture
    def user_service(self):
        return UserService()
    
    @pytest.fixture
    def sample_user_data(self):
        return {
            "email": "test@example.com",
            "name": "Test User",
            "role": "nurse"
        }
    
    def test_create_user_success(self, user_service, sample_user_data):
        user = user_service.create_user(sample_user_data)
        assert user.email == sample_user_data["email"]
        assert user.role == sample_user_data["role"]
    
    def test_create_user_duplicate_email(self, user_service, sample_user_data):
        user_service.create_user(sample_user_data)
        with pytest.raises(ValueError, match="Email already exists"):
            user_service.create_user(sample_user_data)
```

```typescript
// Frontend unit test example
// apps/nurseflow/tests/components/UserForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UserForm } from '../components/UserForm'
import { createMockUser } from '../__mocks__/user'

describe('UserForm', () => {
  test('renders form fields correctly', () => {
    render(<UserForm onSubmit={jest.fn()} />)
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
  })
  
  test('submits form with valid data', async () => {
    const mockSubmit = jest.fn()
    render(<UserForm onSubmit={mockSubmit} />)
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    })
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: 'Test User' }
    })
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        name: 'Test User'
      })
    })
  })
})
```

#### Phase 3: Integration Test Implementation
```python
# Backend integration test example
# firebase-functions/tests/test_user_integration.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.user import User
from app.database import get_db

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("postgresql://test:test@localhost/testdb")
    TestingSessionLocal = sessionmaker(autocommit=False, bind=engine)
    User.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    engine.dispose()

@pytest.fixture
def client(test_db):
    def override_get_db():
        return test_db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

class TestUserIntegration:
    def test_create_user_endpoint(self, client):
        response = client.post("/api/users", json={
            "email": "test@example.com",
            "name": "Test User",
            "role": "nurse"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    def test_get_user_endpoint(self, client):
        # First create a user
        create_response = client.post("/api/users", json={
            "email": "test@example.com",
            "name": "Test User",
            "role": "nurse"
        })
        user_id = create_response.json()["id"]
        
        # Then retrieve the user
        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
```

#### Phase 4: E2E Test Implementation
```typescript
// E2E test example
// apps/nurseflow/tests/e2e/user-journey.spec.ts
import { test, expect } from '@playwright/test'

test.describe('User Journey', () => {
  test('user can register and access dashboard', async ({ page }) => {
    // Navigate to registration
    await page.goto('/register')
    
    // Fill registration form
    await page.fill('[data-testid="email-input"]', 'test@example.com')
    await page.fill('[data-testid="name-input"]', 'Test User')
    await page.fill('[data-testid="password-input"]', 'SecurePass123!')
    await page.selectOption('[data-testid="role-select"]', 'nurse')
    
    // Submit registration
    await page.click('[data-testid="register-button"]')
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Verify dashboard elements
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Test User')
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
  })
  
  test('user can login and access profile', async ({ page }) => {
    // Navigate to login
    await page.goto('/login')
    
    // Fill login form
    await page.fill('[data-testid="email-input"]', 'test@example.com')
    await page.fill('[data-testid="password-input"]', 'SecurePass123!')
    
    // Submit login
    await page.click('[data-testid="login-button"]')
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Navigate to profile
    await page.click('[data-testid="profile-menu"]')
    await expect(page).toHaveURL('/profile')
    
    // Verify profile data
    await expect(page.locator('[data-testid="profile-email"]')).toHaveText('test@example.com')
    await expect(page.locator('[data-testid="profile-name"]')).toHaveText('Test User')
  })
})
```

### 🛠️ TEST AUTOMATION & CI/CD

#### GitHub Actions Integration
```yaml
# .github/workflows/testing.yml
name: Testing Pipeline

on:
  push:
    branches: [ main, develop, staging ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          cd firebase-functions
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-postgresql pytest-cov
      
      - name: Run unit tests
        run: |
          cd firebase-functions
          python -m pytest tests/unit/ -v --cov=app --cov-report=xml --cov-fail-under=80
      
      - name: Run integration tests
        run: |
          cd firebase-functions
          python -m pytest tests/integration/ -v --cov=app --cov-report=xml --cov-append
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./firebase-functions/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [nurseflow, admin, english-exam]
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: apps/${{ matrix.app }}/package-lock.json
      
      - name: Install dependencies
        run: |
          cd apps/${{ matrix.app }}
          npm ci
      
      - name: Run unit tests
        run: |
          cd apps/${{ matrix.app }}
          npm run test -- --coverage
      
      - name: Run build test
        run: |
          cd apps/${{ matrix.app }}
          npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install Playwright
        run: npm install -g @playwright/test
      
      - name: Install dependencies
        run: |
          cd apps/nurseflow
          npm ci
          npx playwright install
      
      - name: Run E2E tests
        run: |
          cd apps/nurseflow
          npx playwright test tests/e2e/
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: apps/nurseflow/playwright-report
```

### 📊 COVERAGE REPORTING & METRICS

#### Coverage Targets
- **Backend**: ≥80% lines, ≥90% for core modules
- **Frontend**: ≥80% statements, ≥85% for components
- **Integration**: ≥75% API coverage
- **E2E**: 100% critical path coverage

#### Quality Gates
- All tests must pass before merge
- Coverage must meet minimum targets
- No flaky tests allowed in CI
- Performance tests must meet timing targets

#### Reporting Tools
- **Codecov**: Coverage visualization and tracking
- **GitHub Actions**: Test results and artifacts
- **Playwright**: E2E test reports and screenshots
- **Coverage Badges**: README status badges

### 🧪 TEST DATA MANAGEMENT

#### Factories & Fixtures
```python
# Backend test factories
# firebase-functions/tests/factories.py
import factory
from app.models.user import User

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')
    role = factory.Iterator(['nurse', 'doctor', 'admin'])
    is_active = True
```

```typescript
// Frontend test factories
// apps/nurseflow/tests/__mocks__/user.ts
export const createMockUser = (overrides = {}) => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  role: 'nurse',
  isActive: true,
  createdAt: new Date().toISOString(),
  ...overrides
})
```

#### Test Data Management
- **Database**: Fresh database for each test run
- **API**: Mocked external services
- **Files**: Temporary test files cleaned up after tests
- **State**: Reset state between tests

### 🔧 TEST EXECUTION COMMANDS

#### Local Testing
```bash
# Backend tests
cd firebase-functions
python -m pytest tests/ -v --cov=app

# Frontend tests
cd apps/nurseflow
npm run test

# E2E tests
cd apps/nurseflow
npm run playwright:test

# All tests with coverage
npm run test:coverage
```

#### CI Testing
```bash
# Run specific test types
pytest tests/unit/ --cov=app
pytest tests/integration/ --cov=app --cov-append
npm run test:unit
npm run test:e2e

# Generate coverage reports
pytest --cov=app --cov-report=html
npm run test:coverage
```

### 📈 PERFORMANCE & QUALITY METRICS

#### Test Performance Targets
- **Unit Tests**: <30s total execution time
- **Integration Tests**: <2m total execution time
- **E2E Tests**: <5m total execution time
- **CI Pipeline**: <10m total execution time

#### Quality Metrics
- **Test Reliability**: >95% pass rate
- **Flaky Test Rate**: <1%
- **Coverage Trend**: Increasing or stable
- **Test Execution Time**: Stable or improving

### 🚨 TROUBLESHOOTING GUIDE

#### Common Issues & Solutions

1. **Test Database Issues**
   - Ensure PostgreSQL test container is running
   - Check database connection strings
   - Verify test data cleanup

2. **Frontend Test Failures**
   - Check Node.js version compatibility
   - Verify test environment setup
   - Review component mounting issues

3. **E2E Test Flakiness**
   - Increase test timeouts
   - Add explicit waits for dynamic content
   - Use test IDs instead of CSS selectors

4. **Coverage Issues**
   - Check for uncovered critical paths
   - Review test coverage configuration
   - Add tests for uncovered modules

5. **CI Pipeline Failures**
   - Check GitHub Actions logs
   - Verify environment variables
   - Review test execution order

### 📋 MAINTENANCE SCHEDULE

#### Daily (Automated)
- Run full test suite on all pushes
- Generate coverage reports
- Monitor test performance metrics

#### Weekly (Manual Review)
- Review test coverage trends
- Identify flaky tests
- Update test documentation

#### Monthly (Manual Review)
- Review test pyramid balance
- Update test targets and goals
- Optimize test performance

---

## Test Summary  
| Layer | Count | Duration | Coverage | Notes |  
|:--|:--|:--|:--|:--|  
| Unit | 150+ | <30s | ≥80% | ✅ Pass |  
| Integration | 50+ | <2m | ≥75% | ✅ Pass |  
| E2E | 5 | <5m | 100% | ✅ Pass |  

## Validation  
✅ All tests pass  
✅ Coverage ≥ target  
✅ CI green  

## Assumptions  
- GitHub Actions CI with PostgreSQL test containers  
- Node.js 18+ for frontend testing  
- Test data factories and fixtures implemented  
- Coverage reporting via Codecov and GitHub Actions

## CHECKLIST  
- [x] Pyramid ratio balanced  
- [x] Coverage logged  
- [x] CI green  
- [x] No flaky tests  
- [x] Report saved

---

*Last updated: 2025-10-29*
*Contact: QA team for testing issues and improvements*
