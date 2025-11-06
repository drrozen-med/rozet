---
description: Diagnose and fix front-end ↔ back-end bugs systematically
---

tac-bug-hunt

Purpose: Diagnose and fix front-end ↔ back-end bugs systematically.
Scope Level: Standard
Overview:
This template walks through capture, compare, repair, and verify.



A — AIM  
Find and resolve the root cause of a data or UI bug in the Next.js ↔ FastAPI stack.

B — BUILDING BLOCKS  
Gather: user repro steps, console errors, network traces, BE logs.  
Tools: Chrome DevTools MCP, Postman, pytest.  
Compare request ↔ response ↔ UI expectations.

C — CLARITY & CHECKPOINTS  
Success = reproducible cause identified + verified fix.

WORKFLOW  
1. Capture evidence (screens, logs, network).  
2. Compare FE/BE contracts.  
3. Propose hypothesis & patch.  
4. Re-run scenario; confirm clean console/network.  
5. Produce “Root Cause → Fix → Proof” markdown summary.
