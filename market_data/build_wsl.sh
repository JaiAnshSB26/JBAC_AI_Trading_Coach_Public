#!/bin/bash
# WSL Build Script - Run this in WSL with Docker installed

set -e

echo "🐳 Building Market Data Lambda with Docker (Linux binaries)..."

# Get the Windows path and convert to WSL path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Building Docker image..."
docker build -t lambda-market-data-builder .

echo "🏗️  Creating container and extracting package..."
docker create --name lambda-builder-temp lambda-market-data-builder
docker cp lambda-builder-temp:/tmp/lambda_package.zip ./lambda_package.zip
docker rm lambda-builder-temp

# Get file size
SIZE=$(stat -c%s lambda_package.zip)
SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)

echo ""
echo "✅ Package built successfully!"
echo "📦 File: lambda_package.zip"
echo "📊 Size: ${SIZE_MB}MB"
echo ""
echo "Now run this command to deploy (you can run it from Windows or WSL):"
echo "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip"
