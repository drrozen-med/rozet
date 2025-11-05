# MCP DevTools Integration Module

**Version:** 1.0  
**Purpose:** Enforce browser-based verification for web development  
**Severity:** HIGH  
**Applies To:** Agents working on web/UI/API tasks

---

## Core Principle

**IF YOU WRITE UI/API CODE, YOU MUST VERIFY IT IN A BROWSER/CLIENT.**

Never claim web features work without visual/network verification.

---

## Mandatory MCP DevTools Usage

### For ANY Web UI Work

**Required Steps:**
1. Implement feature
2. Start development server
3. Open browser via MCP
4. Navigate to feature
5. Check console for errors
6. Verify visual appearance
7. Take screenshot
8. Report findings

### For ANY API Work

**Required Steps:**
1. Implement endpoint
2. Start server
3. Test with curl/MCP
4. Check response status
5. Verify response body
6. Check server logs
7. Report findings

---

## MCP Browser Verification Pattern

```
Step 1: Implementation
[Code written]

Step 2: Server Start
Command: npm run dev
Output: Server running on http://localhost:3000

Step 3: Browser Verification (MCP)
[MCP] Opening http://localhost:3000/feature
[MCP] Checking console...
Console Output:
  ✓ No errors
  ✓ No warnings
  
[MCP] Inspecting network tab...
Network Requests:
  ✓ GET /api/users - 200 OK (143ms)
  ✓ POST /api/login - 200 OK (89ms)
  
[MCP] Taking screenshot...
[Screenshot attached]

Step 4: Visual Verification
✓ Button renders correctly
✓ Form submits successfully  
✓ Loading state displays
✓ Error messages show properly

Conclusion: Feature working as expected in browser.
```

---

## Console Error Checking (Mandatory)

**ALWAYS check browser console:**

```
[MCP] Checking console for errors...

Errors Found:
🚨 TypeError: Cannot read property 'map' of undefined
   at UserList.js:23
   Cause: API returned null instead of array

Warnings Found:
🟡 Warning: Each child in list should have unique key
   at UserList.js:45
   
Next: Fixing both issues...
```

---

## Network Tab Verification (Mandatory for API)

**ALWAYS check network requests:**

```
[MCP] Inspecting network tab...

Request: POST /api/users
Status: 500 Internal Server Error
Response: {"error": "Database connection failed"}

Issue Detected: Backend not connecting to database.
Next: Checking database configuration...
```

---

## Screenshot Evidence (Required for UI)

**ALWAYS take screenshots of implemented features:**

```
[MCP] Taking screenshot of login form...
[Screenshot: login-form.png]

Visual Verification:
✓ Form fields visible
✓ Submit button styled correctly
✓ Error message placeholder present
✗ Logo not centered (needs CSS fix)

Next: Adjusting logo alignment...
```

---

## Quick Reference

### When to Use MCP DevTools

| Task Type | MCP Required? | What to Check |
|-----------|---------------|---------------|
| Add UI component | YES | Console, Visual, Screenshot |
| Modify CSS | YES | Visual, Screenshot |
| Create API endpoint | YES | Network tab, Response |
| Fix bug in frontend | YES | Console, Behavior |
| Update backend logic | OPTIONAL | Can use curl instead |

---

## Configuration

```json
{
  "mcp_devtools": {
    "enabled": true,
    "require_for_ui": true,
    "require_for_api": true,
    "check_console": true,
    "check_network": true,
    "take_screenshots": true,
    "verify_visuals": true
  }
}
```

---

## Summary

**Core Message:** Use browser dev tools to verify web work. Don't guess if it works - CHECK in browser.

**Pattern:** Code → Start Server → Open Browser → Check Console/Network → Screenshot → Report

**Goal:** Catch visual/network bugs immediately, ensure features actually work in browser.
