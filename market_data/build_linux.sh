#!/bin/bash
# Build Lambda package on Linux using Docker to avoid Windows/Linux binary compatibility issues

set -e

echo "🐳 Building Market Data Lambda package using Docker (Linux environment)..."

cd "$(dirname "$0")"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t lambda-market-data-builder .

# Create a container and copy the zip file out
echo "📤 Extracting package..."
docker create --name temp-container lambda-market-data-builder
docker cp temp-container:/tmp/lambda_package.zip ./lambda_package.zip
docker rm temp-container

# Get file size
if [[ "$OSTYPE" == "darwin"* ]]; then
    SIZE=$(stat -f%z lambda_package.zip)
else
    SIZE=$(stat -c%s lambda_package.zip)
fi
SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)

echo "✅ Package built successfully!"
echo "📦 File: lambda_package.zip"
echo "📊 Size: ${SIZE_MB}MB"
echo ""
echo "To deploy, run:"
echo "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip"
