# 🔐 Security Configuration Guide

## ⚠️ IMPORTANT: Required Configuration Before Deployment

This is a **PUBLIC REPOSITORY** and contains **NO sensitive credentials**. You must configure your own API keys and credentials before running this application.

## 📋 Required Credentials Checklist

### 1. AWS Credentials

You need an AWS account with the following services configured:

#### AWS Access Keys
- **AWS_ACCESS_KEY_ID**: Your AWS access key
- **AWS_SECRET_ACCESS_KEY**: Your AWS secret key
- **AWS_REGION**: Default is `us-east-1`

**How to get them:**
1. Log into AWS Console: https://console.aws.amazon.com
2. Navigate to IAM → Users → Your User → Security Credentials
3. Create Access Key → Application running outside AWS
4. Save both the Access Key ID and Secret Access Key

**Required IAM Permissions:**
- `dynamodb:*` - For DynamoDB operations
- `bedrock:InvokeModel` - For AWS Bedrock LLM access
- `lambda:InvokeFunction` - For Lambda function invocation
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` - For CloudWatch logging

#### DynamoDB Tables
Create these tables in AWS DynamoDB:
- **Users** - Primary Key: `user_id` (String)
- **Portfolios** - Primary Key: `portfolio_id` (String)
- **Trades** - Primary Key: `trade_id` (String)

### 2. Google OAuth Client ID

For user authentication via Google:

**How to get it:**
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Create a new project or select existing one
3. Navigate to APIs & Services → Credentials
4. Click "Create Credentials" → OAuth 2.0 Client ID
5. Application type: Web application
6. Add Authorized JavaScript origins:
   - `http://localhost:4200` (development)
   - `http://YOUR_DOMAIN` (production)
7. Add Authorized redirect URIs:
   - `http://localhost:4200/auth/callback`
   - `http://YOUR_DOMAIN/auth/callback`
8. Copy the Client ID (format: `xxxxx-xxxxx.apps.googleusercontent.com`)

**Where to configure:**
- Backend: `backend/.env` → `GOOGLE_CLIENT_ID`
- Frontend: `ui/src/environments/environment.ts` → `googleClientId`
- Frontend Prod: `ui/src/environments/environment.prod.ts` → `googleClientId`

### 3. JWT Secret

For securing authentication tokens:

**Generate a secure random string:**
```bash
# Option 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Option 3: Using PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

**Where to configure:**
- `backend/.env` → `JWT_SECRET`

### 4. (Optional) Market Data API Keys

If you want real-time market data beyond yfinance:

- **Polygon.io**: https://polygon.io/ → `POLYGON_API_KEY`
- **Alpha Vantage**: https://www.alphavantage.co/ → `ALPHA_VANTAGE_KEY`
- **Twelve Data**: https://twelvedata.com/ → `TWELVEDATA_KEY`

> **Note**: The application works with yfinance (free) by default. These are optional for enhanced data.

---

## 🛠️ Configuration Steps

### Step 1: Backend Configuration

Create `backend/.env` file:

```bash
# Copy the example file
cp backend/.env.example backend/.env

# Edit with your credentials
nano backend/.env
```

Required content:
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY

# DynamoDB Tables
DYNAMODB_TABLE_USERS=Users
DYNAMODB_TABLE_PLANS=jbac-plans
DYNAMODB_TABLE_SIMULATIONS=jbac-simulations

# Google OAuth
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET

# JWT Secret (generate a secure random string)
JWT_SECRET=YOUR_SECURE_JWT_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api
CORS_ORIGINS=http://localhost:4200,http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Storage
USE_LOCAL_STORAGE=false

# (Optional) Market Data APIs
POLYGON_API_KEY=
ALPHA_VANTAGE_KEY=
TWELVEDATA_KEY=
```

### Step 2: Frontend Configuration

Edit `ui/src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  googleClientId: 'YOUR_GOOGLE_CLIENT_ID'
};
```

Edit `ui/src/environments/environment.prod.ts`:
```typescript
export const environment = {
  production: true,
  apiUrl: 'http://YOUR_DOMAIN/api',
  googleClientId: 'YOUR_GOOGLE_CLIENT_ID'
};
```

### Step 3: Lambda Configuration (Optional)

If deploying Lambda functions, create `.env.lambda`:
```bash
LAMBDA_MARKET_DATA_FUNCTION=jbac-market-data
LAMBDA_LLM_AGENTS_FUNCTION=jbac-llm-agents
USE_LAMBDA_FUNCTIONS=false
AWS_REGION=us-east-1
```

---

## 🚨 Security Best Practices

### ✅ DO:
- Store `.env` files locally only (never commit to Git)
- Use environment variables for all sensitive data
- Rotate AWS credentials regularly
- Use AWS IAM roles with minimum required permissions
- Enable MFA on AWS account
- Use HTTPS in production
- Keep dependencies updated

### ❌ DON'T:
- Commit `.env` files to Git
- Share credentials in chat/email
- Use the same JWT secret across environments
- Hardcode API keys in source code
- Use root AWS credentials
- Disable CORS in production without restrictions

---

## 🔍 Files That Should NEVER Be Committed

The `.gitignore` file prevents these from being committed:
- `.env` and `.env.*` (except `.env.example`)
- `*.pem` - AWS SSH keys
- `*.key` - Private keys
- `credentials.json` - Any credentials files
- `secrets.json` - Any secrets files

---

## 📝 Environment Files Included in Repo

These are **SAFE** to commit (no secrets):
- `backend/.env.example` - Template for backend config
- `ui/.env.example` - Template for frontend config
- `.env.lambda` - Lambda function names only

---

## 🧪 Testing Your Configuration

### Backend
```bash
cd backend
python check_config.py
```

This will verify:
- All required environment variables are set
- AWS credentials are valid
- DynamoDB tables are accessible
- Google OAuth client ID is configured

### Frontend
```bash
cd ui
npm run start
```
Check browser console for configuration errors.

---

## 🆘 Troubleshooting

### "AWS credentials not found"
- Check `.env` file exists in `backend/` directory
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Test with: `aws sts get-caller-identity`

### "DynamoDB table not found"
- Create tables in AWS Console
- Verify table names match `.env` configuration
- Check AWS region is correct

### "Google OAuth error"
- Verify Client ID is correct
- Check authorized origins in Google Cloud Console
- Ensure redirect URIs are configured

### "JWT decode error"
- Regenerate JWT_SECRET
- Clear browser localStorage
- Restart backend server

---

## 📞 Support

For security issues or questions about configuration:
1. Check this guide first
2. Review `.env.example` files for all required variables
3. Test each service independently (AWS, Google OAuth, etc.)
4. Check application logs for specific error messages

---

## 🔄 Rotating Credentials

If credentials are compromised:

1. **AWS Keys:**
   - Deactivate old keys in IAM Console
   - Generate new access keys
   - Update `.env` file
   - Restart backend

2. **Google OAuth:**
   - Delete old Client ID in Google Cloud Console
   - Create new OAuth credentials
   - Update environment files
   - Rebuild frontend

3. **JWT Secret:**
   - Generate new secret
   - Update `.env`
   - All users will need to re-login

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All credentials are configured in production environment
- [ ] `.env` files are NOT in Git repository
- [ ] AWS IAM permissions are set to minimum required
- [ ] Google OAuth redirect URIs include production domain
- [ ] JWT secret is strong and unique
- [ ] HTTPS is enabled
- [ ] CORS origins are restricted to your domains
- [ ] CloudWatch logging is enabled
- [ ] DynamoDB backup is configured
- [ ] Regular credential rotation schedule is set

---

**Remember**: Security is not a one-time setup. Regularly review and update your configuration! 🔒
