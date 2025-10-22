#!/bin/bash
# Create IAM role for Lambda functions

ROLE_NAME="lambda-basic-execution"
REGION="us-east-1"

echo "🔐 Creating IAM role for Lambda..."

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

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "✅ Role $ROLE_NAME already exists"
else
    echo "🆕 Creating role $ROLE_NAME..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json
    
    echo "📎 Attaching basic execution policy..."
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    echo "⏳ Waiting for role to propagate (10 seconds)..."
    sleep 10
    
    echo "✅ Role created successfully!"
fi

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
echo "📋 Role ARN: $ROLE_ARN"
