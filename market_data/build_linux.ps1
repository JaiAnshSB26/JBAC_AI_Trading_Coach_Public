# PowerShell script to build Lambda package on Linux using Docker
# This avoids Windows/Linux binary compatibility issues

Write-Host "🐳 Building Market Data Lambda package using Docker (Linux environment)..." -ForegroundColor Cyan

Set-Location $PSScriptRoot

# Build the Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -t lambda-market-data-builder .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

# Create a container and copy the zip file out
Write-Host "📤 Extracting package..." -ForegroundColor Yellow
docker create --name temp-container lambda-market-data-builder
docker cp temp-container:/tmp/lambda_package.zip ./lambda_package.zip
docker rm temp-container

# Get file size
$size = (Get-Item lambda_package.zip).Length
$sizeMB = [math]::Round($size / 1MB, 2)

Write-Host ""
Write-Host "✅ Package built successfully!" -ForegroundColor Green
Write-Host "📦 File: lambda_package.zip" -ForegroundColor Cyan
Write-Host "📊 Size: ${sizeMB}MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "To deploy, run:" -ForegroundColor Yellow
Write-Host "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip" -ForegroundColor White
