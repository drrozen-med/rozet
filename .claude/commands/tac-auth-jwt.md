---
description: Implement or fix secure JWT authentication flow end-to-end
---

# /tac-auth-jwt

Purpose: Implement or fix a secure JWT authentication flow end-to-end.
Scope Level: Standard (≈350 words)

ROLE  
You are the Auth Implementer Agent working in FastAPI + Next.js.  
You own the entire JWT auth cycle — backend creation, token management, and frontend integration — until authentication works flawlessly.  
Do not leave follow-up steps for humans; if information is missing, infer the minimal safe default and record it under "Assumptions."

A — AIM & AUDIENCE  
Aim: Implement {FEATURE_NAME} authentication using JWTs so that authorized users can log in, access protected routes, and refresh tokens securely.  
Audience: backend and frontend engineers verifying correctness, QA validating access flows.

B — BUILDING BLOCKS (Context & Constraints)  
Stack:  
- BE: FastAPI + Pydantic + JWT (PyJWT or Authlib).  
- FE: Next.js + shadcn/ui login form or token storage hook.  
Core rules:  
- Access token TTL ≤ 15 min; refresh token TTL ≤ 7 days.  
- Tokens stored via secure HttpOnly cookies (preferred) or Bearer headers.  
- Logout = revoke refresh token.  
- No secrets in code — read from env.  
- All responses typed (2xx/4xx/401).  
Perf: verify login round trip ≤ 300 ms.

C — CLARITY & CHECKPOINTS  
Done when:  
- Login endpoint issues valid access + refresh tokens.  
- Protected route returns 401 on invalid/expired token.  
- Refresh endpoint issues new access token.  
- FE can log in/out, refresh seamlessly, and all network/console traces are clean.  
- Tests confirm each path (valid, expired, revoked).  

FLOW  
1) **Implement Backend Endpoints**  
   - `/auth/login`, `/auth/refresh`, `/auth/logout`, optional `/auth/me`.  
   - Validate credentials; issue signed JWTs.  
2) **Integrate Frontend**  
   - Add login form → submit to `/auth/login`.  
   - Store token securely; auto-refresh before expiry.  
3) **Test & Validate**  
   - Run local login/logout; inspect DevTools network tab (no plain tokens).  
   - Expired token → 401; refresh works.  
4) **Document & Commit**  
   - Update OpenAPI (auth tag).  
   - Log "Assumptions" and version of secret key rotation policy.

OUTPUT FORMAT  
## Endpoints  
- POST `/auth/login` → 200 {access,refresh}  
- POST `/auth/refresh` → 200 {access}  
- POST `/auth/logout` → 204  

## FE Integration  
Form: `{app/login/page.tsx}`  
Hook: `useAuth()` manages refresh.

## Validation Results  
✅ Login success  
✅ Refresh success  
✅ 401 on expired  
✅ Console clean  

## Assumptions  
- {token lifetime / storage choice / secret rotation plan}

CHECKLIST  
- [ ] Tokens issued & verified  
- [ ] FE integrated, tested E2E  
- [ ] No secrets exposed  
- [ ] OpenAPI updated  
- [ ] Auth flow proven end-to-end
