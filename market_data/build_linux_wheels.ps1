# Alternative build approach: Download pre-built Linux wheels
# This avoids the need for Docker

Write-Host "📦 Building Market Data Lambda package (Linux-compatible)..." -ForegroundColor Cyan

Set-Location $PSScriptRoot

# Clean up old package
if (Test-Path "package") { Remove-Item -Recurse -Force package }
if (Test-Path "lambda_package.zip") { Remove-Item -Force lambda_package.zip }

# Create package directory
New-Item -ItemType Directory -Force -Path "package" | Out-Null

# Download Linux wheels for Lambda (Python 3.11, manylinux)
Write-Host "⬇️  Downloading Linux-compatible packages..." -ForegroundColor Yellow
pip download `
    --only-binary=:all: `
    --platform manylinux2014_x86_64 `
    --python-version 3.11 `
    --implementation cp `
    --abi cp311 `
    -r requirements.txt `
    -d package/

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to download packages!" -ForegroundColor Red
    exit 1
}

# Extract all wheels
Write-Host "📦 Extracting packages..." -ForegroundColor Yellow
Set-Location package

Get-ChildItem -Filter "*.whl" | ForEach-Object {
    Write-Host "  Extracting $($_.Name)..." -ForegroundColor Gray
    Expand-Archive -Path $_.FullName -DestinationPath . -Force
    Remove-Item $_.FullName
}

# Copy handler
Copy-Item ..\handler.py .

# Clean up unnecessary files
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter "*.dist-info" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter "tests" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

# Create zip
Write-Host "📦 Creating zip file..." -ForegroundColor Yellow
Compress-Archive -Path * -DestinationPath ..\lambda_package.zip -Force

Set-Location ..
Remove-Item -Recurse -Force package

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
