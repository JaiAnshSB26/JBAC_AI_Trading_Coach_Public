#!/bin/bash
# Complete deployment and test script for Market Data Lambda

set -e

FUNCTION_NAME="jbac-market-data"
REGION="us-east-1"

echo "========================================="
echo "Market Data Lambda - Deploy & Test"
echo "========================================="
echo ""

# Step 1: Create IAM role if it doesn't exist
echo "Step 1: Checking IAM role..."
ROLE_NAME="lambda-basic-execution"

if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null > /dev/null; then
    echo "✅ Role $ROLE_NAME exists"
else
    echo "Creating IAM role..."
    
    # Create trust policy
    cat > /tmp/lambda-trust-policy.json <<EOF
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
EOF
    
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json
    
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    echo "⏳ Waiting 10 seconds for role to propagate..."
    sleep 10
fi

# Get role ARN
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "📋 Using Role: $ROLE_ARN"
echo ""

# Step 2: Build and deploy Lambda
echo "Step 2: Building Lambda package..."
cd lambdas/market_data

# Clean
rm -rf package deployment.zip

# Create package directory
mkdir -p package

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t package/ --upgrade --quiet

# Copy handler
cp handler.py package/

# Create zip
echo "Creating deployment package..."
cd package
zip -r ../deployment.zip . -q
cd ..

SIZE=$(du -sh deployment.zip | cut -f1)
echo "📦 Package size: $SIZE"
echo ""

# Step 3: Deploy to AWS
echo "Step 3: Deploying to AWS Lambda..."
cd ../..

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null > /dev/null; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://lambdas/market_data/deployment.zip" \
        --region "$REGION" > /dev/null
    
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 60 \
        --memory-size 512 \
        --region "$REGION" > /dev/null
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler handler.lambda_handler \
        --zip-file "fileb://lambdas/market_data/deployment.zip" \
        --timeout 60 \
        --memory-size 512 \
        --region "$REGION" > /dev/null
fi

echo "✅ Deployment complete!"
echo ""

# Step 4: Test the Lambda
echo "Step 4: Testing Lambda function..."
echo ""

# Test 1: Get latest price for AAPL
echo "Test 1: Get latest price for AAPL"
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{"action":"get_latest","symbol":"AAPL"}' \
    --region "$REGION" \
    response.json > /dev/null

echo "Response:"
cat response.json | python3 -m json.tool
echo ""

# Test 2: Get candles for TSLA
echo "Test 2: Get candles for TSLA (5 days)"
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{"action":"get_candles","symbol":"TSLA","period":"5d"}' \
    --region "$REGION" \
    response.json > /dev/null

echo "Response (first candle):"
cat response.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps({'count': data['count'], 'first_candle': data['candles'][0] if data['candles'] else None}, indent=2))"
echo ""

# Test 3: Get with indicators
echo "Test 3: Get candles with indicators for NVDA"
aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload '{"action":"get_with_indicators","symbol":"NVDA","period":"1mo"}' \
    --region "$REGION" \
    response.json > /dev/null

echo "Response (latest with indicators):"
cat response.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps({'count': data['count'], 'latest': data['candles'][-1] if data['candles'] else None}, indent=2))"
echo ""

echo "========================================="
echo "✅ All tests complete!"
echo "========================================="
echo ""
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "To invoke manually:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"action\":\"get_latest\",\"symbol\":\"AAPL\"}' response.json --region $REGION"
