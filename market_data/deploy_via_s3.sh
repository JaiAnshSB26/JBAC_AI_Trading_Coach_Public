#!/bin/bash
# Deploy Lambda package via S3 (for packages > 50MB)

set -e

FUNCTION_NAME="jbac-market-data"
PACKAGE_FILE="lambda_package.zip"
S3_BUCKET="jbac-lambda-packages"  # Change this if you have a different bucket
S3_KEY="market-data/lambda_package_$(date +%Y%m%d_%H%M%S).zip"

cd "$(dirname "$0")"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Package file not found: $PACKAGE_FILE"
    echo "Run build_wsl.sh first!"
    exit 1
fi

echo "📦 Deploying package: $PACKAGE_FILE"

# Check if S3 bucket exists, create if not
echo "🪣 Checking S3 bucket..."
if ! aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
    echo "Creating S3 bucket: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET"
fi

# Upload to S3
echo "⬆️  Uploading to S3: s3://$S3_BUCKET/$S3_KEY"
aws s3 cp "$PACKAGE_FILE" "s3://$S3_BUCKET/$S3_KEY"

# Update Lambda function
echo "🚀 Updating Lambda function: $FUNCTION_NAME"
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$S3_KEY"

echo ""
echo "✅ Lambda function updated successfully!"
echo ""
echo "To test, run:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"action\":\"get_latest\",\"symbol\":\"AAPL\"}' response.json"
