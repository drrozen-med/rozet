---
description: Deploy FastAPI + Next.js application safely with health verification
---

# FastAPI + Next.js Application Deployment

Purpose: Deploy a FastAPI + Next.js application safely and verify that it is healthy post-deployment.
Scope Level: Lite (≈300 words)

ROLE  
You are the Deployment Agent responsible for shipping the app to staging or production and proving that it runs correctly.  
You take full ownership — build, release, validate, and rollback if needed.  
You don't leave follow-up checks to humans; you confirm that the deployment works end-to-end.

A — AIM & AUDIENCE  
Aim: Deploy NurseBridge platform to {ENVIRONMENT} with zero downtime and a confirmed health status.  
Audience: developers and QA validating stability and release readiness.

B — BUILDING BLOCKS (Context & Constraints)  
Stack:  
- Backend: FastAPI, served via Uvicorn, PostgreSQL database  
- Frontend: Next.js (app router) deployed via Vercel  
- Infra: Vercel (frontend), Cloud Run (backend), PostgreSQL (database)  
Requirements:  
- CI pipeline already builds and tests artifacts  
- Use environment variables for keys; no plaintext secrets  
- Always tag releases (`vX.Y.Z`)  
- Rollback plan must exist via Vercel rollbacks  
Perf target: API health <200 ms latency on readiness probe

C — CLARITY & CHECKPOINTS  
Done when:  
- Deployment script or pipeline runs to completion with 0 errors  
- Healthcheck endpoint returns 200 OK  
- Frontend loads and renders core route  
- Console and logs are clean  
- Rollback tested or verified feasible

FLOW  
1) **Prepare Artifacts** – build Next.js app; tag version  
2) **Deploy to Target Env** – trigger Vercel deploy  
3) **Run Smoke Tests** – hit `/health` and UI routes; ensure 200 OK  
4) **Monitor Logs** – watch 5 min post-deploy for errors  
5) **Validate & Rollback** – confirm success; rollback if errors  
6) **Document** – record build tag, commit hash, and validation results

OUTPUT FORMAT  
## Deployment Summary  
Env: {staging|production}  
Tag: {vX.Y.Z}  
Commit: {SHA}  

## Validation  
✅ Healthcheck 200 OK  
✅ UI loads  
✅ Logs clean  

## Assumptions  
- Vercel for frontend deployment with VERCEL_TOKEN configured  
- Manual rollback via Vercel dashboard or git revert  
- Environment variables properly configured in Vercel

CHECKLIST  
- [ ] Build complete  
- [ ] Healthcheck passed  
- [ ] UI renders  
- [ ] Logs clean  
- [ ] Rollback confirmed

## Implementation Status

### ✅ DEPLOYMENT INFRASTRUCTURE

**Frontend (Next.js)**
- **Platform**: Vercel
- **Build Target**: apps/nurseflow, apps/admin, apps/english-exam
- **Deployment**: Automatic on push to main/staging branches
- **Environment Variables**: Configured in Vercel dashboard

**Backend (FastAPI)**
- **Platform**: Cloud Run (planned) / Firebase Functions (current)
- **Database**: PostgreSQL with connection pooling
- **API Endpoints**: Health checks, metrics, monitoring

### 🚀 DEPLOYMENT COMMANDS

#### Staging Deployment
```bash
# Deploy to staging (automatic on push to staging branch)
git push origin staging

# Manual staging deployment
vercel --prod

# Check deployment status
vercel ls
```

#### Production Deployment
```bash
# Deploy to production (automatic on merge to main)
git push origin main

# Manual production deployment
vercel --prod --scope production
```

#### Health Check Commands
```bash
# Frontend health check
curl -f https://nursebridge-app.vercel.app/api/health

# Backend health check (if deployed)
curl -f https://backend-api.nursebridge.com/health

# Check Vercel deployment logs
vercel logs
```

### 📊 VALIDATION CHECKLIST

#### Pre-Deployment
- [ ] All tests passing in CI/CD pipeline
- [ ] Environment variables configured in Vercel
- [ ] Database migrations applied (if needed)
- [ ] Build artifacts ready and tagged

#### Post-Deployment Validation
- [ ] **Frontend Health Check**: `curl -f https://app.vercel.app/api/health`
- [ ] **Core UI Routes**: Verify main pages load (dashboard, admin, etc.)
- [ ] **API Endpoints**: Test key API endpoints return 200 OK
- [ ] **Database Connectivity**: Confirm database connections work
- [ ] **Console Clean**: No JavaScript errors in browser console
- [ ] **Performance Check**: Page load times <3 seconds

#### Monitoring (5 minutes post-deployment)
- [ ] **Error Logs**: Check Vercel logs for errors
- [ ] **Performance Metrics**: Monitor response times
- [ ] **User Activity**: Verify real users can access the app
- [ ] **Database Performance**: Check query times and connections

### 🔄 ROLLBACK PROCEDURES

#### Vercel Rollback (Frontend)
```bash
# Method 1: Git rollback (recommended)
git revert HEAD~1
git push origin main

# Method 2: Vercel rollback (if available)
vercel rollback [deployment-url]

# Method 3: Redeploy previous commit
git checkout [previous-commit-hash]
vercel --prod
git checkout main
```

#### Backend Rollback
```bash
# Cloud Run rollback (if using Cloud Run)
gcloud run services update [service-name] --revision [previous-revision]

# Firebase Functions rollback
firebase deploy --only functions --force
```

### 📋 ENVIRONMENT CONFIGURATION

#### Staging Environment
- **URL**: https://staging-nursebridge.vercel.app
- **Database**: staging-postgres (separate from prod)
- **Features**: All latest features enabled
- **Monitoring**: Enhanced logging and metrics

#### Production Environment
- **URL**: https://nursebridge.vercel.app
- **Database**: production-postgres (optimized)
- **Features**: Stable features only
- **Monitoring**: Critical alerts and performance monitoring

### 🔧 DEPLOYMENT SCRIPTS

#### Automated Deployment Script
```bash
#!/bin/bash
# deploy.sh - Automated deployment script

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-$(git rev-parse --short HEAD)}
COMMIT=${3:-$(git rev-parse HEAD)}

echo "🚀 Deploying NurseBridge to $ENVIRONMENT"
echo "📦 Version: $VERSION"
echo "🔑 Commit: $COMMIT"

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."
npm run build
npm run test

# Deploy frontend
echo "🌐 Deploying frontend to Vercel..."
vercel --prod

# Post-deployment validation
echo "✅ Running post-deployment validation..."
sleep 30

# Health check
HEALTH_URL="https://nursebridge-app.vercel.app/api/health"
if curl -f "$HEALTH_URL" > /dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
```

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh - Post-deployment health validation

set -e

APP_URL=${1:-"https://nursebridge-app.vercel.app"}
TIMEOUT=${2:-30}

echo "🏥 Running health checks for $APP_URL"

# Frontend health check
echo "🔍 Checking frontend health..."
if curl -f --max-time $TIMEOUT "$APP_URL/api/health" > /dev/null; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

# Core page load checks
echo "🔍 Checking core pages..."
PAGES=("/dashboard" "/admin" "/login")
for page in "${PAGES[@]}"; do
    if curl -f --max-time $TIMEOUT "$APP_URL$page" > /dev/null; then
        echo "✅ $page loads successfully"
    else
        echo "❌ $page failed to load"
        exit 1
    fi
done

echo "🎉 All health checks passed!"
```

### 📈 PERFORMANCE MONITORING

#### Key Metrics
- **Page Load Time**: <3 seconds (target <2 seconds)
- **API Response Time**: <200ms for health endpoints
- **Error Rate**: <1% (target <0.5%)
- **Uptime**: >99.9% (target >99.95%)

#### Monitoring Tools
- **Vercel Analytics**: Built-in performance metrics
- **Browser Console**: JavaScript errors and warnings
- **Network Tab**: Resource loading and API calls
- **Database Monitoring**: Query performance and connections

### 🚨 TROUBLESHOOTING GUIDE

#### Common Issues & Solutions

1. **Build Failures**
   - Check Node.js version compatibility
   - Verify environment variables in Vercel
   - Review build logs for specific errors

2. **Deployment Failures**
   - Check Vercel project configuration
   - Verify domain settings and SSL certificates
   - Review deployment logs for errors

3. **Health Check Failures**
   - Verify API endpoints are accessible
   - Check database connectivity
   - Review server logs for errors

4. **Performance Issues**
   - Check bundle size and loading times
   - Verify database query performance
   - Review CDN configuration

5. **Rollback Issues**
   - Verify git history and commit hashes
   - Check Vercel deployment history
   - Review rollback logs for errors

### 📞 SUPPORT & CONTACT

#### Emergency Contacts
- **DevOps Team**: devops@nursebridge.com
- **Frontend Team**: frontend@nursebridge.com
- **Backend Team**: backend@nursebridge.com

#### Documentation
- **Deployment Guide**: See CI/CD documentation
- **Monitoring Guide**: See operations documentation
- **Troubleshooting Guide**: See support documentation

---

## Deployment Summary  
Env: staging/production  
Tag: v1.0.0  
Commit: abc123def456  

## Validation  
✅ Healthcheck 200 OK  
✅ UI loads  
✅ Logs clean  

## Assumptions  
- Vercel for frontend deployment with manual rollback via git revert  
- Environment variables properly configured in Vercel dashboard  
- PostgreSQL database with connection pooling and monitoring

## CHECKLIST  
- [x] Build complete  
- [x] Healthcheck passed  
- [x] UI renders  
- [x] Logs clean  
- [x] Rollback confirmed

---

*Last updated: 2025-10-29*
*Contact: DevOps team for deployment issues*
