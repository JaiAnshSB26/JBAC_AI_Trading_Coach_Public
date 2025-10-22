# Cleanup script for EC2 deployment
Write-Host "🧹 Cleaning up repository for EC2 deployment..." -ForegroundColor Cyan

# Create backup first
$backupDir = "backup_before_cleanup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "📦 Creating backup: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Backup important Lambda files
Write-Host "📦 Backing up Lambda files..." -ForegroundColor Yellow
Copy-Item -Path "lambda_handler.py" -Destination "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item -Path "lambdas/" -Destination "$backupDir/" -Recurse -ErrorAction SilentlyContinue
Copy-Item -Path "requirements-lambda.txt" -Destination "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item -Path "requirements-lambda-minimal.txt" -Destination "$backupDir/" -ErrorAction SilentlyContinue

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
Remove-Item -Path "test_all_lambdas.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "test_deployed_lambdas.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "test_dynamo.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "verify_deployment.py" -Force -ErrorAction SilentlyContinue

# Remove old documentation (keep only EC2_DEPLOYMENT.md and README.md)
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

# Remove backend agents (logic is in Lambda now)
Write-Host "🗑️  Removing backend agents (now in Lambda)..." -ForegroundColor Yellow
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

Write-Host ""
Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host "📦 Backup saved in: $backupDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Repository size:" -ForegroundColor Cyan
$size = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Current size: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create requirements-ec2.txt" -ForegroundColor White
Write-Host "2. Create backend/services/lambda_invoker.py" -ForegroundColor White
Write-Host "3. Simplify backend/app.py for Lambda proxying" -ForegroundColor White
Write-Host "4. Test locally" -ForegroundColor White
Write-Host "5. Commit and push to GitHub" -ForegroundColor White
Write-Host "6. Deploy to EC2" -ForegroundColor White
