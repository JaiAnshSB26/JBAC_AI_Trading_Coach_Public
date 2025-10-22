# EC2 Cleanup Plan - Remove Clutter for Free Tier Deployment

## Goal
Keep only essential files for EC2 deployment (Angular frontend + minimal backend to invoke Lambda).
Lambda functions are already deployed, so we don't need the full backend logic on EC2.

---

## Files/Folders to KEEP ✅

### Frontend (Essential)
- `ui/` - Entire Angular application
  - `src/`
  - `angular.json`
  - `package.json`
  - `tsconfig.json`
  - etc.

### Backend (Minimal - Lambda Invocation Only)
- `backend/app.py` - FastAPI entry point (simplified for Lambda invoke)
- `backend/config.py` - Configuration
- `backend/domain.py` - Domain models (if needed for types)
- `backend/services/` - Keep only Lambda invoke wrappers
  - `auth_service.py` - If handling JWT locally
  - `lambda_invoker.py` - NEW: Wrapper to call Lambda functions

### Infrastructure & Docs
- `EC2_DEPLOYMENT.md` - Deployment guide
- `README.md` - Project overview
- `requirements-ec2.txt` - NEW: Minimal EC2 requirements (boto3, fastapi, uvicorn)
- `.gitignore`

---

## Files/Folders to REMOVE ❌

### Lambda Deployment Files (Already Deployed)
- `lambda_handler.py` - Already in Lambda
- `deploy_lambda_package.py` - No longer needed
- `deploy_lambda.ps1` - No longer needed
- `deploy_lambda.sh` - No longer needed
- `build_lambda_docker.ps1` - No longer needed
- `build_lambda_docker.sh` - No longer needed
- `requirements-lambda.txt` - No longer needed
- `requirements-lambda-minimal.txt` - No longer needed
- `lambda_package/` - Build artifacts
- `lambdas/` - Lambda source (already deployed)
- `test_all_lambdas.py` - Testing scripts
- `test_deployed_lambdas.py` - Testing scripts
- `test_dynamo.py` - Testing scripts
- `verify_deployment.py` - Testing scripts

### Documentation (Already Completed)
- `LAMBDA_ARCHITECTURE.md` - Reference only
- `LAMBDA_SUCCESS.md` - Reference only
- `DEPLOYMENT.md` - Old deployment docs
- `PRODUCTION_READY.md` - Consolidated into EC2 guide
- `CORS_GUIDE.md` - Reference only
- `YFINANCE_SETUP.md` - Not needed for EC2
- `MODEL_COMPARISON.md` - Reference only
- `DB_SCHEMA.md` - Reference only
- `SETUP.md` - Old setup guide
- `AGENT_COLLABORATION.md` - Development notes

### Development Files
- `implementation.txt` - Development notes
- `llm.txt` - Development notes
- `next_steps.txt` - Completed
- `todo.txt` - Completed
- `response.json` - Test artifact
- `fix-after-pull.ps1` - No longer needed

### Virtual Environment & Build Artifacts
- `markets/` - Virtual environment (recreate on EC2)
- `temp_check/` - Temporary files
- `backend/__pycache__/` - Python cache
- `backend/agents/` - Logic already in Lambda
- `backend/eval/` - Evaluation scripts

### Infrastructure (Not Needed for EC2)
- `docker/` - Docker files (not using Docker on EC2)
- `infra/` - EC2 user data (integrated into EC2_DEPLOYMENT.md)
- `scripts/create_dynamodb_tables.py` - Already created

---

## NEW Files to Create

### 1. `requirements-ec2.txt` - Minimal EC2 Dependencies
```txt
# Minimal dependencies for EC2 FastAPI server
fastapi==0.111.0
uvicorn[standard]==0.30.0
boto3==1.34.155
pydantic==2.8.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
google-auth==2.16.0
PyJWT==2.8.0
```

### 2. `backend/services/lambda_invoker.py` - Lambda Invoke Wrapper
```python
import json
import boto3
from typing import Dict, Any

lambda_client = boto3.client('lambda', region_name='us-east-1')

async def invoke_lambda(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke a Lambda function and return the response.
    
    Args:
        function_name: Name of the Lambda function
        payload: Dictionary to send as payload
    
    Returns:
        Parsed JSON response from Lambda
    """
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# Helper functions for specific Lambda invocations
async def invoke_market_data_lambda(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke market data Lambda function"""
    return await invoke_lambda('jbac-market-data', payload)

async def invoke_ai_agent_lambda(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke AI agent Lambda function"""
    return await invoke_lambda('jbac-ai-agent', payload)

async def invoke_portfolio_lambda(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke portfolio Lambda function"""
    return await invoke_lambda('jbac-portfolio', payload)
```

### 3. Simplified `backend/app.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="JBAC Trading Coach API")

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ec2-api"}

# Import routes that proxy to Lambda
from backend.routes import auth, market, portfolio, ai_agent

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(ai_agent.router, prefix="/ai", tags=["ai"])
```

---

## Cleanup Script

### PowerShell Script: `cleanup_for_ec2.ps1`
```powershell
# Cleanup script for EC2 deployment
Write-Host "🧹 Cleaning up repository for EC2 deployment..." -ForegroundColor Cyan

# Create backup first
$backupDir = "backup_before_cleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "📦 Creating backup: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Backup important files
Copy-Item -Path "lambda_handler.py" -Destination "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item -Path "lambdas/" -Destination "$backupDir/" -Recurse -ErrorAction SilentlyContinue

# Remove Lambda deployment files
Write-Host "🗑️  Removing Lambda deployment files..." -ForegroundColor Yellow
Remove-Item -Path "lambda_handler.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "deploy_lambda_package.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "deploy_lambda.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "deploy_lambda.sh" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build_lambda_docker.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build_lambda_docker.sh" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "requirements-lambda.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "requirements-lambda-minimal.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "lambda_package/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "lambdas/" -Recurse -Force -ErrorAction SilentlyContinue

# Remove test files
Write-Host "🗑️  Removing test files..." -ForegroundColor Yellow
Remove-Item -Path "test_*.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "verify_deployment.py" -Force -ErrorAction SilentlyContinue

# Remove documentation (keep only EC2_DEPLOYMENT.md and README.md)
Write-Host "🗑️  Removing old documentation..." -ForegroundColor Yellow
Remove-Item -Path "LAMBDA_ARCHITECTURE.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "LAMBDA_SUCCESS.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "DEPLOYMENT.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "PRODUCTION_READY.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "CORS_GUIDE.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "YFINANCE_SETUP.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "MODEL_COMPARISON.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "DB_SCHEMA.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "SETUP.md" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "AGENT_COLLABORATION.md" -Force -ErrorAction SilentlyContinue

# Remove development files
Write-Host "🗑️  Removing development files..." -ForegroundColor Yellow
Remove-Item -Path "implementation.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "llm.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "next_steps.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "todo.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "response.json" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "fix-after-pull.ps1" -Force -ErrorAction SilentlyContinue

# Remove temp files
Write-Host "🗑️  Removing temporary files..." -ForegroundColor Yellow
Remove-Item -Path "temp_check/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/__pycache__/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/agents/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend/eval/" -Recurse -Force -ErrorAction SilentlyContinue

# Remove infrastructure files
Write-Host "🗑️  Removing infrastructure files..." -ForegroundColor Yellow
Remove-Item -Path "docker/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "infra/" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "scripts/" -Recurse -Force -ErrorAction SilentlyContinue

# Remove virtual environment (will recreate on EC2)
Write-Host "🗑️  Removing virtual environment..." -ForegroundColor Yellow
Remove-Item -Path "markets/" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host "📦 Backup saved in: $backupDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Repository size reduction:" -ForegroundColor Cyan
$size = (Get-ChildItem -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Current size: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
```

---

## What Remains After Cleanup

```
JBAC_AI_Trading_Coach/
├── ui/                          # Angular frontend (entire folder)
├── backend/
│   ├── app.py                   # Simplified FastAPI app
│   ├── config.py                # Configuration
│   ├── domain.py                # Domain models
│   ├── routes/                  # NEW: API routes that call Lambda
│   │   ├── auth.py
│   │   ├── market.py
│   │   ├── portfolio.py
│   │   └── ai_agent.py
│   └── services/
│       ├── lambda_invoker.py    # NEW: Lambda invoke wrapper
│       └── auth_service.py      # JWT handling (if local)
├── EC2_DEPLOYMENT.md            # Deployment guide
├── README.md                    # Project overview
├── requirements-ec2.txt         # Minimal EC2 dependencies
├── .gitignore
└── backup_before_cleanup_*/     # Backup of removed files
```

---

## Estimated Size Reduction

**Before cleanup:** ~500-800 MB (with markets venv, lambda_package, etc.)
**After cleanup:** ~20-50 MB (just source code)

This will:
- ✅ Fit easily in EC2 free tier (20 GB storage)
- ✅ Fast git clone/pull on EC2
- ✅ Quick deployments
- ✅ Clear separation: Lambda = business logic, EC2 = frontend + API proxy

---

## Next Steps

1. **Review** the cleanup plan above
2. **Run** `cleanup_for_ec2.ps1` to remove files
3. **Create** new minimal files (requirements-ec2.txt, lambda_invoker.py, routes/)
4. **Test locally** that frontend can still call backend → Lambda
5. **Commit and push** cleaned repo
6. **Deploy to EC2** using EC2_DEPLOYMENT.md

---

## Rollback Plan

If something goes wrong:
- Backup folder created: `backup_before_cleanup_YYYYMMDD_HHMMSS/`
- Git history intact (can revert commit)
- Lambda functions still deployed (unaffected)
