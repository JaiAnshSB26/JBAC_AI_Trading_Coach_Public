# Create IAM role for Lambda functions (PowerShell)

$ROLE_NAME = "lambda-basic-execution"
$REGION = "us-east-1"

Write-Host "🔐 Creating IAM role for Lambda..." -ForegroundColor Green

# Create trust policy
$TRUST_POLICY = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$TRUST_POLICY | Out-File -FilePath "$env:TEMP\lambda-trust-policy.json" -Encoding UTF8

# Check if role exists
try {
    aws iam get-role --role-name $ROLE_NAME 2>$null
    Write-Host "✅ Role $ROLE_NAME already exists" -ForegroundColor Green
} catch {
    Write-Host "🆕 Creating role $ROLE_NAME..." -ForegroundColor Yellow
    aws iam create-role `
        --role-name $ROLE_NAME `
        --assume-role-policy-document "file://$env:TEMP\lambda-trust-policy.json"
    
    Write-Host "📎 Attaching basic execution policy..." -ForegroundColor Yellow
    aws iam attach-role-policy `
        --role-name $ROLE_NAME `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    Write-Host "⏳ Waiting for role to propagate (10 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "✅ Role created successfully!" -ForegroundColor Green
}

# Get role ARN
$ROLE_ARN = (aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
Write-Host "📋 Role ARN: $ROLE_ARN" -ForegroundColor Cyan
