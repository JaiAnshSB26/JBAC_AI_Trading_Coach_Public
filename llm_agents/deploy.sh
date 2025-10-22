#!/bin/bash
# Deploy LLM Agents Lambda Function

set -e

FUNCTION_NAME="jbac-llm-agents"
REGION="us-east-1"
LAMBDA_DIR="lambdas/llm_agents"
PACKAGE_DIR="$LAMBDA_DIR/package"
ZIP_FILE="$LAMBDA_DIR/deployment.zip"

echo "🚀 Deploying LLM Agents Lambda..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$PACKAGE_DIR"
rm -f "$ZIP_FILE"

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Install dependencies (minimal - just boto3)
echo "📦 Installing dependencies..."
pip install -r "$LAMBDA_DIR/requirements.txt" -t "$PACKAGE_DIR" --upgrade

# Copy handler
echo "📋 Copying handler..."
cp "$LAMBDA_DIR/handler.py" "$PACKAGE_DIR/"

# Create deployment package
echo "🗜️  Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r "../deployment.zip" . -q
cd ../../..

# Get package size
SIZE=$(du -sh "$ZIP_FILE" | cut -f1)
echo "📊 Package size: $SIZE"

# Check if function exists
echo "🔍 Checking if function exists..."
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null; then
    echo "♻️  Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION"
    
    echo "⚙️  Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0}" \
        --region "$REGION"
else
    echo "🆕 Creating new function..."
    
    # Get AWS account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler handler.lambda_handler \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0}" \
        --region "$REGION"
fi

echo "✅ Deployment complete!"
echo ""
echo "📝 Test the function with:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"agent\":\"coach\",\"messages\":[{\"role\":\"user\",\"content\":\"What is RSI?\"}],\"max_tokens\":500}' response.json --region $REGION"
