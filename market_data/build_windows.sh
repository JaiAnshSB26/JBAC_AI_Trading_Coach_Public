#!/bin/bash
# Simple build script that works in Git Bash

set -e

echo "Building Market Data Lambda package..."

cd "$(dirname "$0")"

# Clean up
rm -rf package lambda_package.zip

# Create package directory
mkdir -p package
cd package

# Install dependencies
echo "Installing dependencies..."
pip install -t . -r ../requirements.txt

# Copy handler
cp ../handler.py .

# Clean up
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Create zip
echo "Creating zip file..."
zip -r ../lambda_package.zip . > /dev/null

cd ..
rm -rf package

SIZE=$(stat -c%s lambda_package.zip 2>/dev/null || stat -f%z lambda_package.zip 2>/dev/null || wc -c < lambda_package.zip)
SIZE_MB=$(echo "scale=2; $SIZE / 1048576" | bc 2>/dev/null || python -c "print(f'{$SIZE/1048576:.2f}')")

echo ""
echo "Package built: lambda_package.zip (${SIZE_MB}MB)"
echo ""
echo "⚠️  WARNING: This package contains Windows-built binaries!"
echo "   It will likely fail on Lambda (Linux environment)."
echo "   You need to build on Linux, use Docker, or use Lambda Layers."
echo ""
echo "To deploy anyway (for testing), run:"
echo "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip"
