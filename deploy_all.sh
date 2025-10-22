#!/bin/bash
# Quick deployment script - Run all Lambda deployments

set -e

echo "========================================="
echo "🚀 JBAC Lambda Deployment Suite"
echo "========================================="
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Step 1: Create IAM role (if needed)
echo "Step 1: Checking IAM role..."
if aws iam get-role --role-name lambda-basic-execution 2>/dev/null > /dev/null; then
    echo "✅ IAM role exists"
else
    echo "Creating IAM role..."
    bash lambdas/create_iam_role.sh
fi
echo ""

# Step 2: Deploy Market Data Lambda
echo "Step 2: Deploying Market Data Lambda..."
bash lambdas/market_data/test_deploy.sh
echo ""

# Step 3: Deploy LLM Agents Lambda
echo "Step 3: Deploying LLM Agents Lambda..."
bash lambdas/llm_agents/deploy.sh
echo ""

# Step 4: Add Bedrock permissions to Lambda role
echo "Step 4: Adding Bedrock permissions..."
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
    --policy-document file:///tmp/bedrock-policy.json 2>/dev/null || echo "⚠️  Bedrock policy may already exist"

echo "✅ Bedrock permissions added"
echo ""

# Step 5: Test LLM Agents Lambda
echo "Step 5: Testing LLM Agents Lambda..."
aws lambda invoke \
    --function-name jbac-llm-agents \
    --payload '{"agent":"coach","messages":[{"role":"user","content":"What is RSI in simple terms?"}],"max_tokens":300}' \
    --region us-east-1 \
    response.json > /dev/null

echo "Response:"
cat response.json | python3 -m json.tool
echo ""

# Step 6: Display summary
echo "========================================="
echo "✅ All Lambda Functions Deployed!"
echo "========================================="
echo ""
echo "📊 Deployed Functions:"
echo "  1. jbac-market-data (512MB, 60s timeout)"
echo "  2. jbac-llm-agents (256MB, 30s timeout)"
echo ""
echo "🔗 Integration:"
echo "  Update your .env file with:"
echo "  USE_LAMBDA_FUNCTIONS=true"
echo "  LAMBDA_MARKET_DATA_FUNCTION=jbac-market-data"
echo "  LAMBDA_LLM_AGENTS_FUNCTION=jbac-llm-agents"
echo ""
echo "📝 Next Steps:"
echo "  1. Run backend with Lambda integration"
echo "  2. Monitor CloudWatch logs"
echo "  3. Check costs in AWS Cost Explorer"
echo ""
echo "🎉 Deployment complete!"
