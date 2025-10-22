# Deploy Market Data Lambda Function (PowerShell)

$FUNCTION_NAME = "jbac-market-data"
$REGION = "us-east-1"
$LAMBDA_DIR = "lambdas/market_data"
$PACKAGE_DIR = "$LAMBDA_DIR/package"
$ZIP_FILE = "$LAMBDA_DIR/deployment.zip"

Write-Host "🚀 Deploying Market Data Lambda..." -ForegroundColor Green

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path $PACKAGE_DIR) { Remove-Item -Recurse -Force $PACKAGE_DIR }
if (Test-Path $ZIP_FILE) { Remove-Item -Force $ZIP_FILE }

# Create package directory
New-Item -ItemType Directory -Force -Path $PACKAGE_DIR | Out-Null

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r "$LAMBDA_DIR/requirements.txt" -t $PACKAGE_DIR --upgrade

# Copy handler
Write-Host "📋 Copying handler..." -ForegroundColor Yellow
Copy-Item "$LAMBDA_DIR/handler.py" -Destination "$PACKAGE_DIR/"

# Create deployment package
Write-Host "🗜️  Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path "$PACKAGE_DIR/*" -DestinationPath $ZIP_FILE -Force

# Get package size
$SIZE = (Get-Item $ZIP_FILE).Length / 1MB
Write-Host "📊 Package size: $([math]::Round($SIZE, 2)) MB" -ForegroundColor Cyan

# Check if function exists
Write-Host "🔍 Checking if function exists..." -ForegroundColor Yellow
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null
    $EXISTS = $true
} catch {
    $EXISTS = $false
}

if ($EXISTS) {
    Write-Host "♻️  Updating existing function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file "fileb://$ZIP_FILE" `
        --region $REGION
    
    Write-Host "⚙️  Updating function configuration..." -ForegroundColor Yellow
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --timeout 60 `
        --memory-size 512 `
        --region $REGION
} else {
    Write-Host "🆕 Creating new function..." -ForegroundColor Yellow
    
    # Get AWS account ID
    $ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
    $ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"
    
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime python3.11 `
        --role $ROLE_ARN `
        --handler handler.lambda_handler `
        --zip-file "fileb://$ZIP_FILE" `
        --timeout 60 `
        --memory-size 512 `
        --region $REGION
}

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Test the function with:" -ForegroundColor Cyan
Write-Host "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"action\":\"get_latest\",\"symbol\":\"AAPL\"}' response.json --region $REGION" -ForegroundColor White
