# Lambda Deployment Guide

## 🔐 IMPORTANT: Security Configuration Required

**This is a public repository with NO embedded credentials.** Before deploying, you must configure your own:
- AWS Access Keys
- Google OAuth Client ID
- JWT Secret
- DynamoDB Tables

**👉 See [SECURITY.md](SECURITY.md) for complete setup instructions.**

---

## 🎯 Overview

This guide helps you deploy individual Lambda functions for the JBAC AI Trading Coach, replacing the monolithic Lambda deployment with modular, lightweight functions.

## 📁 Structure

```
lambdas/
├── market_data/          # Heavy: yfinance + pandas + numpy
│   ├── handler.py
│   ├── requirements.txt
│   ├── deploy.sh
│   └── test_deploy.sh
│
├── llm_agents/           # Light: boto3 only (Bedrock)
│   ├── handler.py
│   ├── requirements.txt
│   └── deploy.sh
│
└── create_iam_role.sh    # IAM setup script
```

## 🚀 Quick Start

### Step 1: Create IAM Role

```bash
# Check if role exists
aws iam get-role --role-name lambda-basic-execution

# If not, create it
bash lambdas/create_iam_role.sh
```

### Step 2: Deploy Market Data Lambda

```bash
# Deploy and test in one command
bash lambdas/market_data/test_deploy.sh
```

**What it does:**
- Packages yfinance, pandas, numpy (~60MB)
- Deploys to `jbac-market-data` function
- Runs 3 test cases (latest price, candles, indicators)
- Shows response times and data

**Expected Output:**
```json
{
  "latest": {
    "time": "2025-10-20T00:00:00",
    "close": 178.52,
    "volume": 45234567
  }
}
```

### Step 3: Deploy LLM Agents Lambda

```bash
cd lambdas/llm_agents

# Clean and build
rm -rf package deployment.zip
mkdir package
pip install -r requirements.txt -t package/
cp handler.py package/
cd package && zip -r ../deployment.zip . && cd ..

# Deploy
FUNCTION_NAME="jbac-llm-agents"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"

aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler handler.lambda_handler \
    --zip-file fileb://deployment.zip \
    --timeout 30 \
    --memory-size 256 \
    --region $REGION \
    --environment "Variables={BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0}"

# Test it
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"agent":"coach","messages":[{"role":"user","content":"What is RSI?"}],"max_tokens":500}' \
    --region $REGION \
    response.json

cat response.json | python3 -m json.tool
```

**Expected Output:**
```json
{
  "agent": "coach",
  "response": "RSI (Relative Strength Index) is a momentum indicator...",
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

## 📊 Lambda Comparison

| Function | Size | Cold Start | Runtime | Cost/1M |
|----------|------|------------|---------|---------|
| **Full Backend** | ~200MB | 8-15s | 512MB | $8.33 |
| **Market Data** | ~60MB | 2-4s | 512MB | $2.77 |
| **LLM Agents** | ~5MB | <1s | 256MB | $0.42 |

**Savings: ~75% reduction in costs** 💰

## 🧪 Testing Each Lambda

### Market Data Tests

```bash
# Test 1: Get latest price
aws lambda invoke \
    --function-name jbac-market-data \
    --payload '{"action":"get_latest","symbol":"AAPL"}' \
    --region us-east-1 \
    response.json

# Test 2: Get candles with indicators
aws lambda invoke \
    --function-name jbac-market-data \
    --payload '{"action":"get_with_indicators","symbol":"TSLA","period":"1mo"}' \
    --region us-east-1 \
    response.json
```

### LLM Agent Tests

```bash
# Test Coach
aws lambda invoke \
    --function-name jbac-llm-agents \
    --payload '{"agent":"coach","messages":[{"role":"user","content":"Explain EMA"}],"max_tokens":500}' \
    --region us-east-1 \
    response.json

# Test Planner
aws lambda invoke \
    --function-name jbac-llm-agents \
    --payload '{"agent":"planner","messages":[{"role":"user","content":"Goal: Learn options trading\nRisk: moderate\nSymbols: [\"SPY\",\"AAPL\"]\nReturn JSON with levels -> lessons"}],"max_tokens":700}' \
    --region us-east-1 \
    response.json

# Test Critic
aws lambda invoke \
    --function-name jbac-llm-agents \
    --payload '{"agent":"critic","messages":[{"role":"user","content":"Symbol: AAPL\nAction: buy\nReason: RSI oversold at 28\nIndicators: {\"close\":175.5,\"rsi\":28,\"ema20\":180,\"ema50\":178}"}],"max_tokens":800}' \
    --region us-east-1 \
    response.json
```

## 🔐 IAM Permissions

### Basic Lambda Execution Role
Created by `create_iam_role.sh`:
- CloudWatch Logs (write)
- Basic Lambda execution

### Additional for LLM Agents
Add Bedrock permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
      ]
    }
  ]
}
```

Apply it:
```bash
# Save above as bedrock-policy.json
aws iam put-role-policy \
    --role-name lambda-basic-execution \
    --policy-name BedrockAccess \
    --policy-document file://bedrock-policy.json
```

## 🔄 Integration with Backend

### Option 1: Direct Lambda Invocation (Sync)
```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Call market data lambda
response = lambda_client.invoke(
    FunctionName='jbac-market-data',
    InvocationType='RequestResponse',  # Synchronous
    Payload=json.dumps({
        'action': 'get_latest',
        'symbol': 'AAPL'
    })
)

result = json.loads(response['Payload'].read())
```

### Option 2: Lambda Function URLs (HTTP)
Enable Function URL in AWS Console:
1. Go to Lambda → jbac-market-data → Configuration → Function URL
2. Create Function URL → Auth type: NONE (or AWS_IAM)
3. Get URL: `https://abc123.lambda-url.us-east-1.on.aws/`

Call it:
```python
import requests

response = requests.post(
    'https://abc123.lambda-url.us-east-1.on.aws/',
    json={'action': 'get_latest', 'symbol': 'AAPL'}
)
data = response.json()
```

### Option 3: API Gateway (Recommended for Production)
- Create REST API
- Connect to Lambda functions
- Add rate limiting, caching, auth
- Get custom domain

## 📈 Monitoring

### CloudWatch Logs
```bash
# Market Data logs
aws logs tail /aws/lambda/jbac-market-data --follow

# LLM Agents logs
aws logs tail /aws/lambda/jbac-llm-agents --follow
```

### CloudWatch Metrics
```bash
# Get invocation count (last hour)
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=jbac-market-data \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum
```

## 🐛 Troubleshooting

### Issue: "Role not found"
**Solution:** Wait 10 seconds after creating IAM role, or manually specify ARN:
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/lambda-basic-execution"
```

### Issue: "Package too large"
**Solution:** Market Data Lambda is ~60MB. If over 250MB unzipped:
- Remove unused dependencies
- Use Lambda layers for common packages
- Deploy as container image instead

### Issue: "Bedrock AccessDenied"
**Solution:** Add Bedrock permissions to IAM role (see IAM section above)

### Issue: "yfinance timeout"
**Solution:** Increase Lambda timeout:
```bash
aws lambda update-function-configuration \
    --function-name jbac-market-data \
    --timeout 90
```

## 🎯 Next Steps

1. ✅ Deploy both Lambdas
2. ✅ Test with sample payloads
3. 🔄 Update FastAPI backend to call Lambdas
4. 🌐 Set up API Gateway or Function URLs
5. 📊 Monitor performance and costs
6. 🚀 Profit!

## 💡 Tips

- **Development:** Use Function URLs for quick testing
- **Production:** Use API Gateway with WAF, rate limiting
- **Cost:** Reserved concurrency for predictable workloads
- **Performance:** Provisioned concurrency for <100ms cold starts (extra cost)
- **Debugging:** Enable X-Ray tracing in Lambda configuration

## 📞 Support

If you encounter issues:
1. Check CloudWatch Logs for detailed errors
2. Verify IAM permissions
3. Test locally with same payload structure
4. Check AWS service quotas

---

**Remember:** Each Lambda function is independent and can be updated/deployed separately! 🎉
