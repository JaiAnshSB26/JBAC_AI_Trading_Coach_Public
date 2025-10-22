#!/bin/bash
# Manual Testing Script - Step by step Lambda deployment and testing

echo "========================================="
echo "🧪 Lambda Manual Testing Guide"
echo "========================================="
echo ""
echo "This script will guide you through deploying and testing each Lambda function."
echo "Press ENTER after each step to continue..."
echo ""

# Function to wait for user
wait_for_user() {
    read -p "Press ENTER to continue..."
    echo ""
}

# Step 1: Check AWS CLI
echo "Step 1: Checking AWS CLI and credentials..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

echo "Current AWS Identity:"
aws sts get-caller-identity
echo ""
wait_for_user

# Step 2: Create IAM Role
echo "Step 2: Creating IAM role for Lambda..."
echo "Command:"
echo "  aws iam create-role --role-name lambda-basic-execution --assume-role-policy-document file:///tmp/lambda-trust-policy.json"
echo ""
echo "Creating trust policy..."

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

echo "Checking if role exists..."
if aws iam get-role --role-name lambda-basic-execution 2>/dev/null > /dev/null; then
    echo "✅ Role already exists"
else
    echo "Creating role..."
    aws iam create-role \
        --role-name lambda-basic-execution \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json
    
    echo "Attaching basic execution policy..."
    aws iam attach-role-policy \
        --role-name lambda-basic-execution \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    echo "⏳ Waiting 10 seconds for role to propagate..."
    sleep 10
    echo "✅ Role created"
fi
echo ""
wait_for_user

# Step 3: Build Market Data Lambda
echo "Step 3: Building Market Data Lambda package..."
cd lambdas/market_data

echo "Cleaning previous builds..."
rm -rf package deployment.zip

echo "Creating package directory..."
mkdir -p package

echo "📦 Installing dependencies (this may take 2-3 minutes)..."
pip install -r requirements.txt -t package/ --upgrade --quiet

echo "Copying handler..."
cp handler.py package/

echo "Creating zip file..."
cd package
zip -r ../deployment.zip . -q
cd ..

SIZE=$(du -sh deployment.zip | cut -f1)
echo "✅ Package created: $SIZE"
cd ../..
echo ""
wait_for_user

# Step 4: Deploy Market Data Lambda
echo "Step 4: Deploying Market Data Lambda to AWS..."
FUNCTION_NAME="jbac-market-data"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"

echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Role: $ROLE_ARN"
echo ""

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null > /dev/null; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://lambdas/market_data/deployment.zip" \
        --region "$REGION" > /dev/null
    
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 60 \
        --memory-size 512 \
        --region "$REGION" > /dev/null
    echo "✅ Function updated"
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
    echo "✅ Function created"
fi
echo ""
wait_for_user

# Step 5: Test Market Data Lambda
echo "Step 5: Testing Market Data Lambda..."
echo ""

echo "Test 1: Get latest price for AAPL"
echo "Command: aws lambda invoke --function-name jbac-market-data --payload '{\"action\":\"get_latest\",\"symbol\":\"AAPL\"}' response.json"
aws lambda invoke \
    --function-name jbac-market-data \
    --payload '{"action":"get_latest","symbol":"AAPL"}' \
    --region us-east-1 \
    response.json > /dev/null

echo "Response:"
cat response.json | python3 -m json.tool
echo ""
wait_for_user

echo "Test 2: Get candles for TSLA (5 days)"
aws lambda invoke \
    --function-name jbac-market-data \
    --payload '{"action":"get_candles","symbol":"TSLA","period":"5d"}' \
    --region us-east-1 \
    response.json > /dev/null

echo "Response (count only):"
cat response.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Count: {data.get('count', 0)} candles\")"
echo ""
wait_for_user

# Step 6: Build LLM Agents Lambda
echo "Step 6: Building LLM Agents Lambda package..."
cd lambdas/llm_agents

echo "Cleaning previous builds..."
rm -rf package deployment.zip

echo "Creating package directory..."
mkdir -p package

echo "📦 Installing dependencies (lightweight - just boto3)..."
pip install -r requirements.txt -t package/ --upgrade --quiet

echo "Copying handler..."
cp handler.py package/

echo "Creating zip file..."
cd package
zip -r ../deployment.zip . -q
cd ..

SIZE=$(du -sh deployment.zip | cut -f1)
echo "✅ Package created: $SIZE"
cd ../..
echo ""
wait_for_user

# Step 7: Deploy LLM Agents Lambda
echo "Step 7: Deploying LLM Agents Lambda to AWS..."
FUNCTION_NAME="jbac-llm-agents"

if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null > /dev/null; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://lambdas/llm_agents/deployment.zip" \
        --region "$REGION" > /dev/null
    
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0}" \
        --region "$REGION" > /dev/null
    echo "✅ Function updated"
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler handler.lambda_handler \
        --zip-file "fileb://lambdas/llm_agents/deployment.zip" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0}" \
        --region "$REGION" > /dev/null
    echo "✅ Function created"
fi
echo ""
wait_for_user

# Step 8: Add Bedrock permissions
echo "Step 8: Adding Bedrock permissions to IAM role..."
cat > /tmp/bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name lambda-basic-execution \
    --policy-name BedrockAccess \
    --policy-document file:///tmp/bedrock-policy.json 2>/dev/null && echo "✅ Bedrock permissions added" || echo "⚠️  Policy may already exist"
echo ""
wait_for_user

# Step 9: Test LLM Agents Lambda
echo "Step 9: Testing LLM Agents Lambda..."
echo ""

echo "Test: Ask coach about RSI"
echo "Command: aws lambda invoke --function-name jbac-llm-agents --payload '{\"agent\":\"coach\",\"messages\":[{\"role\":\"user\",\"content\":\"What is RSI?\"}],\"max_tokens\":300}' response.json"
aws lambda invoke \
    --function-name jbac-llm-agents \
    --payload '{"agent":"coach","messages":[{"role":"user","content":"What is RSI in simple terms?"}],"max_tokens":300}' \
    --region us-east-1 \
    response.json > /dev/null

echo "Response:"
cat response.json | python3 -m json.tool
echo ""
wait_for_user

# Step 10: Summary
echo "========================================="
echo "✅ Deployment and Testing Complete!"
echo "========================================="
echo ""
echo "📊 Deployed Functions:"
echo "  1. jbac-market-data"
echo "     - Size: ~60MB"
echo "     - Memory: 512MB"
echo "     - Timeout: 60s"
echo "     - Purpose: Market data + indicators"
echo ""
echo "  2. jbac-llm-agents"
echo "     - Size: ~5MB"
echo "     - Memory: 256MB"
echo "     - Timeout: 30s"
echo "     - Purpose: Bedrock AI agents"
echo ""
echo "🔗 Next Steps:"
echo "  1. Test from your backend using lambda_client.py"
echo "  2. Monitor CloudWatch logs:"
echo "     aws logs tail /aws/lambda/jbac-market-data --follow"
echo "     aws logs tail /aws/lambda/jbac-llm-agents --follow"
echo ""
echo "  3. Check function details:"
echo "     aws lambda get-function --function-name jbac-market-data"
echo "     aws lambda get-function --function-name jbac-llm-agents"
echo ""
echo "  4. Update your backend .env:"
echo "     USE_LAMBDA_FUNCTIONS=true"
echo "     LAMBDA_MARKET_DATA_FUNCTION=jbac-market-data"
echo "     LAMBDA_LLM_AGENTS_FUNCTION=jbac-llm-agents"
echo ""
echo "🎉 All done! Your Lambda functions are live!"
