# Error-First Communication Module

**Version:** 1.0  
**Purpose:** Prioritize error reporting above all else  
**Severity:** CRITICAL  
**Applies To:** All agents

---

## Core Principle

**ERRORS FIRST. ALWAYS. NO EXCEPTIONS.**

If there's an error, report it immediately at the top. Don't bury it. Don't sugarcoat it. Don't hide it in verbose output.

---

## The Error-First Format

### Template

```
[If errors exist]
🚨 ERROR(S) DETECTED:
1. [Error type]: [Exact error message]
   Location: [where]
   Cause: [analysis]
   
2. [Error type]: [Exact error message]
   Location: [where]
   Cause: [analysis]

Next Actions:
- [Specific fix for error 1]
- [Specific fix for error 2]

[If no errors]
✅ No errors detected

[Then normal output]
```

---

## Examples

### Example 1: Command Execution

**❌ BAD (Error Buried):**
```
I ran the migration command to update the database schema. The process started successfully and began applying changes. The system processed 15 migration files and everything looked good initially. However, there was a small issue with the last migration file where it couldn't find the users table, resulting in an error: "Table 'users' doesn't exist". But most of the other migrations worked fine!
```

**✅ GOOD (Error First):**
```
🚨 ERROR: Migration Failed
Error: Table 'users' doesn't exist
Location: migrations/015_add_user_roles.sql
Exit Code: 1

Cause: Migration 015 assumes 'users' table exists, but it wasn't created.

Next Action: Check if migration 014_create_users_table ran successfully.

Full Output:
✓ Migration 001: completed
✓ Migration 002: completed
...
✓ Migration 014: completed
✗ Migration 015: FAILED - Table 'users' doesn't exist
```

### Example 2: Test Results

**❌ BAD:**
```
I ran the test suite and most tests passed. We have good coverage across authentication, API endpoints, and database operations. The system is working well overall. There are 47 passing tests which is great. One test for the edge case handling failed but it's probably just a minor issue.
```

**✅ GOOD:**
```
🚨 TEST FAILURE:
Test: test_null_input_handling
Error: AssertionError: Expected error message, got None
Location: tests/test_api.py:156

Issue: API doesn't handle null input correctly - returns None instead of error.

Test Results:
✗ 1 failing
✓ 47 passing

Next Action: Adding null check to API input validation.
```

### Example 3: Server Start

**❌ BAD:**
```
Starting the development server on port 3000. The server initialized all middleware components and connected to the database successfully. All routes were registered and the API documentation is available at /docs. Oh, and there's a CORS error when trying to access from localhost:8080 but the server itself is running.
```

**✅ GOOD:**
```
🚨 ERROR: CORS Policy Blocking Requests
Error: "Access-Control-Allow-Origin header missing"
Impact: Frontend (localhost:8080) cannot access API

Cause: CORS middleware not configured for localhost:8080

Next Action: Adding localhost:8080 to CORS whitelist.

Server Status:
✓ Server running on port 3000
✓ Database connected
✓ Routes registered
✗ CORS blocking frontend access
```

---

## Error Severity Levels

### 🔴 CRITICAL (Stops functionality)
- Syntax errors
- Server crashes
- Build failures
- Test failures blocking deployment

**Format:**
```
🔴 CRITICAL ERROR: [description]
IMPACT: System non-functional
[details]
```

### 🟡 WARNING (Degrades functionality)
- Deprecation warnings
- Performance issues
- Partial failures
- Missing optional features

**Format:**
```
🟡 WARNING: [description]
IMPACT: Reduced functionality
[details]
```

### 🟢 INFO (FYI, no action needed)
- Successful operations
- Status updates
- Non-blocking notices

**Format:**
```
🟢 INFO: [description]
[details]
```

---

## The 3-Line Error Report

For quick reporting:

```
Line 1: [Error type and message]
Line 2: [Location and cause]
Line 3: [Proposed fix]
```

### Example

```
🚨 TypeError: Cannot read property 'id' of undefined
Location: auth.js:23, Cause: User object is null
Fix: Adding null check before accessing user.id
```

---

## Output Structure

### For Operations With Errors

```
1. 🚨 ERROR SECTION (first, always)
   - All errors listed
   - Causes identified
   - Fixes proposed

2. OPERATION DETAILS
   - What was attempted
   - What succeeded
   - What failed

3. NEXT STEPS
   - Specific actions to fix
```

### For Operations Without Errors

```
1. ✅ SUCCESS CONFIRMATION
   - Clear statement: no errors

2. OPERATION SUMMARY
   - What was done
   - Results

3. VERIFICATION EVIDENCE
   - Test outputs
   - Checks performed
```

---

## Never Minimize Errors

### ❌ Forbidden Phrases

- "just a small error"
- "minor issue"
- "one tiny problem"
- "not a big deal"
- "easily fixable"
- "shouldn't affect anything"

### ✅ Required Approach

State errors objectively without downplaying:

```
ERROR: [exact description]
IMPACT: [actual impact]
NEXT: [concrete fix]
```

---

## Multiple Errors Handling

When multiple errors exist:

```
🚨 MULTIPLE ERRORS DETECTED (3):

1. ERROR: Import failure
   File: api.js:1
   Message: Cannot find module 'express'
   
2. ERROR: Syntax error  
   File: db.js:45
   Message: Unexpected token ':'
   
3. ERROR: Missing file
   File: config.json not found
   Expected location: /app/config.json

Priority Order (most blocking first):
1. Fix import error (blocks execution)
2. Fix syntax error (blocks parsing)
3. Create config file (blocks configuration)

Fixing in order...
```

---

## Error Escalation Protocol

### Level 1: Attempt Fix
- Report error
- Propose fix
- Implement fix
- Verify

### Level 2: Try Alternative
- Report fix didn't work
- Show new error
- Try alternative approach

### Level 3: Request Help
- Report multiple fixes failed
- Show all attempts
- Request user guidance

**Example:**

```
Attempt 1:
🚨 ERROR: Module not found
Fix: npm install express
Result: Same error (npm not installed)

Attempt 2:
🚨 ERROR: npm command not found
Fix: Using yarn instead
Result: Success - module installed

✅ Error resolved via alternative approach
```

---

## Configuration

```json
{
  "error_first_communication": {
    "require_error_at_top": true,
    "show_all_errors": true,
    "prioritize_by_severity": true,
    "include_exact_messages": true,
    "propose_fixes": true,
    "never_minimize_errors": true
  }
}
```

---

## Summary

**Core Message:** If there's an error, say it FIRST. Don't hide it, don't minimize it, don't bury it.

**Pattern:** 
1. Errors (if any) → Always at top
2. Details → Then provide context  
3. Fixes → Then propose solutions

**Goal:** Maximum transparency, fastest error resolution.
