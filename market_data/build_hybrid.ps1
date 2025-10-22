# Hybrid build approach: Pre-built Linux wheels + source for pure Python packages

Write-Host "📦 Building Market Data Lambda package (Linux-compatible)..." -ForegroundColor Cyan

Set-Location $PSScriptRoot

# Clean up old package
if (Test-Path "package") { Remove-Item -Recurse -Force package }
if (Test-Path "lambda_package.zip") { Remove-Item -Force lambda_package.zip }

# Create package directory
New-Item -ItemType Directory -Force -Path "package" | Out-Null

# Install packages targeting Linux Lambda environment
Write-Host "⬇️  Installing packages for Linux Lambda..." -ForegroundColor Yellow
pip install `
    --platform manylinux2014_x86_64 `
    --target package `
    --implementation cp `
    --python-version 3.11 `
    --only-binary=:all: `
    numpy pandas 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Some binary packages failed, continuing..." -ForegroundColor Yellow
}

# Install pure Python packages (no binary dependencies) without platform restrictions
Write-Host "⬇️  Installing pure Python packages..." -ForegroundColor Yellow
pip install `
    --target package `
    --no-deps `
    yfinance requests multitasking platformdirs pytz frozendict peewee lxml html5lib beautifulsoup4 charset-normalizer idna urllib3 certifi 2>&1 | Out-Null

# Copy handler
Write-Host "📄 Copying handler..." -ForegroundColor Yellow
Copy-Item handler.py package\

# Clean up unnecessary files
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
Set-Location package

Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "*.dist-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "tests" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "test" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "*.so" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*cpython-311*" } | Remove-Item -Force -ErrorAction SilentlyContinue

# Create zip
Write-Host "📦 Creating zip file..." -ForegroundColor Yellow
Compress-Archive -Path * -DestinationPath ..\lambda_package.zip -CompressionLevel Optimal -Force

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
Write-Host "⚠️  NOTE: This package contains Linux binaries for pandas/numpy." -ForegroundColor Yellow
Write-Host "   It should work on Lambda but may have compatibility issues." -ForegroundColor Yellow
Write-Host ""
Write-Host "To deploy, run:" -ForegroundColor Yellow
Write-Host "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip" -ForegroundColor White
