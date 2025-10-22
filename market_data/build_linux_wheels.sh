#!/bin/bash
# Alternative build approach: Download pre-built Linux wheels
# This avoids the need for Docker

set -e

echo "📦 Building Market Data Lambda package (Linux-compatible)..."

cd "$(dirname "$0")"

# Clean up old package
rm -rf package lambda_package.zip

# Create package directory
mkdir -p package

# Download Linux wheels for Lambda (Python 3.11, manylinux)
echo "⬇️  Downloading Linux-compatible packages..."
pip download \
    --only-binary=:all: \
    --platform manylinux2014_x86_64 \
    --python-version 3.11 \
    --implementation cp \
    --abi cp311 \
    -r requirements.txt \
    -d package/

# Extract all wheels
echo "📦 Extracting packages..."
cd package
for file in *.whl; do
    if [ -f "$file" ]; then
        unzip -o -q "$file"
        rm "$file"
    fi
done

# Copy handler
cp ../handler.py .

# Clean up unnecessary files
echo "🧹 Cleaning up..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Create zip
echo "📦 Creating zip file..."
zip -r -q ../lambda_package.zip .

cd ..
rm -rf package

# Get file size
SIZE=$(stat -c%s lambda_package.zip 2>/dev/null || stat -f%z lambda_package.zip)
SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)

echo ""
echo "✅ Package built successfully!"
echo "📦 File: lambda_package.zip"
echo "📊 Size: ${SIZE_MB}MB"
echo ""
echo "To deploy, run:"
echo "  aws lambda update-function-code --function-name jbac-market-data --zip-file fileb://lambda_package.zip"
