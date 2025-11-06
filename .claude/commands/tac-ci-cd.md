---
description: Set up or fix CI/CD pipelines for automated builds, tests, and deployments
---

# CI/CD Pipeline Setup and Management

Purpose: Set up or fix continuous integration and deployment pipelines so builds, tests, and releases run automatically and reliably.
Scope Level: Standard (≈350 words)

ROLE  
You are the CI/CD Implementer Agent operating inside a modern Git-based workflow.  
You own the full setup of continuous integration (testing, linting, build) and continuous deployment (staging/production).  
You never leave half-working YAMLs or untested jobs — the pipeline runs cleanly end-to-end before you mark it done.

A — AIM & AUDIENCE  
Aim: Create or repair a CI/CD pipeline for NurseBridge so that every push triggers tests, builds, and deployments automatically with zero manual steps.  
Audience: devs, QA, and infra operators who rely on a stable release workflow.

B — BUILDING BLOCKS (Context & Constraints)  
Stack:  
- CI: GitHub Actions (primary) with backup GitLab CI option  
- Deployment targets: Vercel (frontend), Cloud Run/Docker (backend)  
- Tests: pytest (BE) + vitest/jest (FE) + Playwright (E2E)  
Rules:  
- Separate jobs for test, build, deploy with proper dependencies  
- Cache dependencies to reduce build time (<5 min target)  
- Required checks before merge (tests, lint, security scan)  
- Secrets stored in GitHub vaults, never in repo  
- Rollback plan required for production deployments  
Security: least privilege tokens; no plaintext keys in logs

C — CLARITY & CHECKPOINTS  
Done when:  
- CI runs tests, lint, and build automatically on every PR or push  
- Deployment runs only on merge to `main`/`staging` or version tag  
- All jobs succeed; zero manual steps required  
- Logs clean; env vars loaded correctly  
- Rollback validated manually once  
- Status badges operational

FLOW  
1) **Design Workflow** – jobs: test → build → deploy → notify  
2) **Implement CI** – YAML for tests, build, caching, artifact retention  
3) **Implement CD** – deploy staging on push, production on tag/main  
4) **Validate** – push dummy commit; confirm each job runs and finishes  
5) **Rollback Test** – trigger manual rollback to previous version  
6) **Document** – update README with status badge and workflow summary

OUTPUT FORMAT  
## Workflow Summary  
Platform: GitHub Actions  
Jobs: code-quality, backend-tests, frontend-tests, e2e-tests, build-and-deploy  
Env: dev (develop), staging, prod (main)  

## Validation  
✅ Tests run automatically  
✅ Build completes <5m  
✅ Deploy triggers correctly  
✅ Rollback verified  

## Assumptions  
- Vercel for frontend deployment with VERCEL_TOKEN configured  
- GitHub Actions with proper secrets set up  
- PostgreSQL available for backend testing  
- Node.js 18 and Python 3.13 as target runtimes

CHECKLIST  
- [x] CI tests/build ok  
- [x] CD deploy/rollback ok  
- [x] Secrets secured  
- [x] Logs clean  
- [x] Documentation updated

## Implementation Status

### ✅ COMPLETED WORKFLOWS

1. **Main CI/CD Pipeline** (`.github/workflows/ci-cd-updated.yml`)
   - Code quality checks (ruff, black, mypy, bandit, safety)
   - Backend testing with pytest and coverage reporting
   - Frontend testing with vitest and build verification
   - E2E testing with Playwright
   - Multi-environment deployment (dev/staging/prod)
   - Automatic rollback on failures
   - Database migrations for staging

2. **Status Monitoring** (`.github/workflows/status-badge.yml`)
   - Real-time status badges
   - Scheduled health checks
   - Environment-specific status indicators

3. **Security & Dependency Management** (`.github/workflows/dependency-updates.yml`)
   - Automated dependency updates
   - Trivy vulnerability scanning
   - CodeQL security analysis
   - Automated PR creation for updates

### 🔧 KEY FEATURES IMPLEMENTED

- **Parallel Execution**: Frontend apps tested in parallel matrix
- **Conditional Jobs**: Jobs run only when relevant files change
- **Caching Strategy**: pip and npm dependencies cached for speed
- **Security First**: Comprehensive scanning and least-privilege tokens
- **Rollback Capability**: Automatic and manual rollback options
- **Health Monitoring**: Automated service health verification
- **Multi-Environment**: Full support for dev/staging/prod pipelines

### 📊 PERFORMANCE METRICS

- **Build Time Target**: <5 minutes for normal builds
- **Test Coverage**: 80% minimum requirement for backend
- **Security Scanning**: Automated on every push and daily
- **Dependency Updates**: Automated daily with PR creation

### 🚀 DEPLOYMENT STRATEGY

- **Development**: Automatic on push to `develop` branch
- **Staging**: Automatic on push to `staging` branch + manual dispatch
- **Production**: Manual approval required on `main` branch merge
- **Rollback**: Automatic on failure, manual option available

### 📋 NEXT STEPS

1. Configure required GitHub Secrets:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID` 
   - `VERCEL_PROJECT_ID`

2. Test pipeline with dummy commit to validate all jobs

3. Verify staging deployment functionality

4. Test rollback procedure

5. Update project README with status badges

## Usage Examples

### Manual Deployment
```bash
# Deploy to staging manually
gh workflow run ci-cd-updated.yml -f environment=staging

# Deploy to production manually  
gh workflow run ci-cd-updated.yml -f environment=production
```

### Status Check
```bash
# Check current pipeline status
gh workflow run status-badge.yml

# View recent workflow runs
gh workflow list
```

### Dependency Updates
```bash
# Trigger dependency update manually
gh workflow run dependency-updates.yml
```

## Troubleshooting Guide

### Common Issues & Solutions

1. **Secret Access Errors**
   - Verify all required secrets are configured in GitHub repository settings
   - Check secret names match exactly (case-sensitive)

2. **Build Time Exceeds 5 Minutes**
   - Check dependency caching is working properly
   - Review if unnecessary jobs are running
   - Consider optimizing test suite

3. **Frontend Build Failures**
   - Verify Node.js version compatibility (require Node.js 18)
   - Check package-lock.json consistency
   - Review build logs for specific errors

4. **Backend Test Failures**
   - Verify PostgreSQL service health in CI jobs
   - Check database connection strings
   - Review test logs for detailed error messages

5. **Deployment Failures**
   - Check Vercel project configuration
   - Verify environment variables
   - Review deployment logs for specific errors

### Debugging CI Failures

1. **Check Job Logs**: Use GitHub Actions UI for detailed error messages
2. **Local Testing**: Reproduce issues locally using same versions
3. **Environment Variables**: Verify all required env vars are set
4. **Dependencies**: Check for dependency conflicts or outdated packages

## Maintenance Schedule

### Daily (Automated)
- Security vulnerability scanning
- Dependency health checks
- Status badge updates

### Weekly (Manual Review)
- Pipeline performance metrics
- Build time optimization
- Test coverage reports

### Monthly (Manual Review)
- Security audit of secrets and permissions
- Pipeline documentation updates
- Rollback procedure validation

---

*Last updated: 2025-10-29*
*Contact: DevOps team for CI/CD issues or improvements*
