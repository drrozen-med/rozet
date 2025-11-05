# Anti-Laziness Behavioral Module

**Version:** 1.0  
**Purpose:** Prevents partial implementations, TODO comments, and "will implement later" patterns  
**Severity:** CRITICAL  
**Applies To:** All code-writing agents

---

## Core Principle

**NEVER claim completion without completing the work.**

Every feature request must result in COMPLETE, WORKING code - not placeholders, not TODOs, not sketches.

---

## Prohibited Patterns

### ❌ FORBIDDEN: TODO Comments

```python
# BAD - This is laziness
def process_payment(amount):
    # TODO: implement payment processing
    pass
```

### ❌ FORBIDDEN: Placeholder Implementations

```python
# BAD - This is unacceptable
def authenticate_user(username, password):
    # Will implement authentication later
    return True  # temporary
```

### ❌ FORBIDDEN: Partial Implementations

```python
# BAD - Half-done work
def handle_user_request(request):
    if request.type == "GET":
        return get_handler(request)
    # TODO: handle POST, PUT, DELETE
```

### ❌ FORBIDDEN: "Skeleton" Code

```python
# BAD - Framework without substance
class UserService:
    def create_user(self):
        pass  # implement this
    
    def update_user(self):
        pass  # implement this
    
    def delete_user(self):
        pass  # implement this
```

---

## Required Patterns

### ✅ REQUIRED: Complete Implementations

```python
# GOOD - Full implementation
def process_payment(amount, card_token):
    """Process payment through Stripe API."""
    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),
            currency='usd',
            source=card_token,
            description='Order payment'
        )
        return {
            'success': True,
            'charge_id': charge.id,
            'status': charge.status
        }
    except stripe.error.CardError as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### ✅ REQUIRED: Full Coverage

```python
# GOOD - All cases handled
def handle_user_request(request):
    handlers = {
        'GET': self.get_handler,
        'POST': self.post_handler,
        'PUT': self.put_handler,
        'DELETE': self.delete_handler,
        'PATCH': self.patch_handler
    }
    
    handler = handlers.get(request.type)
    if not handler:
        return {'error': f'Unsupported method: {request.type}'}, 405
    
    return handler(request)
```

### ✅ REQUIRED: Error Handling Included

```python
# GOOD - Edge cases covered
def divide_numbers(a, b):
    """Divide two numbers with proper error handling."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    
    if b == 0:
        raise ValueError("Cannot divide by zero")
    
    return a / b
```

---

## Enforcement Rules

### Rule 1: No Partial Submissions

If you cannot complete a feature fully, you must:
1. State this limitation upfront
2. Explain why completion is blocked
3. Propose alternative approaches
4. Get user approval before proceeding

**Template:**
```
Cannot complete [feature] because [specific blocker].

Options:
1. Implement [reduced scope version] - fully functional but limited
2. Wait for [dependency/information] to implement complete version
3. Use [alternative approach] - different but achieves goal

Which would you prefer?
```

### Rule 2: Mandatory Completeness Check

Before claiming "implemented," verify:

```
Completeness Checklist:
[ ] All promised functionality works
[ ] No TODO comments remain
[ ] No placeholder functions
[ ] Error cases handled
[ ] Edge cases covered
[ ] Tested and verified
```

### Rule 3: If You Start It, Finish It

When you begin implementing a function/class/module:
- Complete ALL its methods
- Handle ALL its edge cases  
- Include ALL error handling
- Test ALL code paths

**Never leave partially implemented structures.**

### Rule 4: Declare Scope Upfront

Before coding, state what you WILL and WON'T implement:

```
Implementation Scope:
WILL IMPLEMENT:
- User authentication with JWT
- Password hashing with bcrypt
- Login endpoint with rate limiting
- Token refresh mechanism

WON'T IMPLEMENT (out of scope):
- OAuth social login
- Two-factor authentication
- Password recovery via email

Proceeding with full implementation of listed features...
```

---

## Detection Patterns

The system monitors for these laziness indicators:

### Code Patterns
- `# TODO:`
- `# FIXME:`
- `# IMPLEMENT:`
- `pass  # ...`
- `raise NotImplementedError`
- `return None  # temporary`

### Language Patterns
- "will implement later"
- "for now, just"
- "basic version"
- "skeleton code"
- "placeholder for"
- "stub implementation"

### Structural Patterns
- Classes with >50% empty methods
- Functions with only `pass`
- Incomplete error handling
- Missing validations

---

## Valid Exceptions

### Exception 1: Deliberate Stubs in Interfaces

When defining an interface/abstract class:

```python
# ACCEPTABLE - Explicit interface definition
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """Abstract base class for payment processors."""
    
    @abstractmethod
    def process_payment(self, amount: float) -> dict:
        """Process a payment. Must be implemented by subclasses."""
        pass
```

**Requirements:**
- Must be explicitly an abstract base class
- Must document that implementation is required
- Must be part of a proper OOP design pattern

### Exception 2: Intentional Feature Flags

When deliberately disabling features:

```python
# ACCEPTABLE - Explicit feature flag
FEATURE_ADVANCED_SEARCH = False  # Will be enabled in v2.0

if FEATURE_ADVANCED_SEARCH:
    # Full implementation exists but is disabled
    results = advanced_search(query)
else:
    results = basic_search(query)
```

**Requirements:**
- Must be clearly marked as feature flag
- Full implementation must exist (just disabled)
- Must document why disabled

### Exception 3: Acknowledged Technical Debt

When accepting technical debt with user agreement:

```python
# ACCEPTABLE - Documented and agreed upon
# TECH DEBT: Currently using linear search O(n)
# TODO: Optimize with binary search O(log n) when dataset > 10k items
# Tracked in issue #1234
def find_user(users, user_id):
    for user in users:
        if user.id == user_id:
            return user
    return None
```

**Requirements:**
- Must be explicitly acknowledged
- Must have tracking ticket
- Must have user sign-off
- Must be limited scope

---

## Configuration Options

Adjust strictness via `config/behavior-settings.json`:

```json
{
  "anti_laziness": {
    "allow_todo_comments": false,
    "allow_pass_statements": false,
    "require_error_handling": true,
    "require_edge_case_coverage": true,
    "minimum_implementation_percentage": 100,
    "exceptions": {
      "abstract_classes": true,
      "feature_flags": true,
      "acknowledged_debt": true
    }
  }
}
```

### Strictness Levels

**Paranoid (Recommended for Production):**
- Zero TODOs allowed
- 100% implementation required
- All edge cases must be covered
- All errors must be handled

**Normal (Balanced):**
- TODOs allowed if tracked
- 95% implementation required
- Major edge cases must be covered
- Critical errors must be handled

**Relaxed (Prototyping Only):**
- TODOs allowed with comments
- 80% implementation required
- Happy path must work
- Fatal errors must be handled

---

## Monitoring Metrics

Track anti-laziness compliance:

```python
{
  "todo_comments": 0,           # Should be 0
  "pass_statements": 2,          # Only in abstract classes
  "incomplete_functions": 0,     # Should be 0
  "unhandled_errors": 0,        # Should be 0
  "implementation_ratio": 1.0    # Should be 1.0 (100%)
}
```

---

## Integration with Orchestrator

The orchestrator can enforce this module by:

1. **Pre-submission scan:** Check for laziness patterns before accepting code
2. **Verification requirement:** Require proof of completeness
3. **Rollback on detection:** Reject code with TODO comments
4. **Escalation:** Route incomplete work to more capable agent

---

## Examples in Context

### Example 1: API Endpoint

**User Request:** "Create a user registration endpoint"

**❌ LAZY Response:**
```python
@app.route('/register', methods=['POST'])
def register():
    # TODO: validate input
    # TODO: check if user exists
    # TODO: hash password
    # TODO: save to database
    return {'status': 'ok'}
```

**✅ COMPLETE Response:**
```python
@app.route('/register', methods=['POST'])
def register():
    """Register a new user with validation and error handling."""
    data = request.get_json()
    
    # Validate input
    required = ['username', 'email', 'password']
    if not all(field in data for field in required):
        return {'error': 'Missing required fields'}, 400
    
    # Validate email format
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
        return {'error': 'Invalid email format'}, 400
    
    # Check password strength
    if len(data['password']) < 8:
        return {'error': 'Password must be at least 8 characters'}, 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return {'error': 'Email already registered'}, 409
    
    # Hash password
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
    
    # Create user
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed
        )
        db.session.add(user)
        db.session.commit()
        
        return {
            'status': 'success',
            'user_id': user.id,
            'username': user.username
        }, 201
        
    except Exception as e:
        db.session.rollback()
        return {'error': 'Registration failed', 'details': str(e)}, 500
```

### Example 2: Class Implementation

**User Request:** "Create a cache manager class"

**❌ LAZY Response:**
```python
class CacheManager:
    def get(self, key):
        # TODO
        pass
    
    def set(self, key, value):
        # TODO
        pass
    
    def delete(self, key):
        # TODO
        pass
```

**✅ COMPLETE Response:**
```python
class CacheManager:
    """Simple in-memory cache with expiration support."""
    
    def __init__(self, default_ttl=300):
        self._cache = {}
        self._expiry = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
    
    def get(self, key):
        """Retrieve value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            if key in self._expiry and time.time() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            
            return self._cache[key]
    
    def set(self, key, value, ttl=None):
        """Store value in cache with expiration."""
        with self._lock:
            self._cache[key] = value
            
            if ttl is None:
                ttl = self.default_ttl
            
            if ttl > 0:
                self._expiry[key] = time.time() + ttl
    
    def delete(self, key):
        """Remove key from cache."""
        with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            now = time.time()
            expired = [k for k, exp_time in self._expiry.items() 
                      if exp_time < now]
            for key in expired:
                del self._cache[key]
                del self._expiry[key]
```

---

## Summary

**Core Message:** Complete every task you start. No TODOs, no placeholders, no promises to "implement later." If you can't complete it, say so upfront and propose alternatives.

**Enforcement:** This module is CRITICAL. Violations should trigger immediate rejection and re-attempt with full implementation.

**Goal:** Production-ready code on first attempt, every time.
