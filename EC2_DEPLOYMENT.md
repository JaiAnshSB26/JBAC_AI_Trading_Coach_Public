# EC2 Deployment Guide - JBAC Trading Coach

## Overview
Deploy the full-stack application (Angular + FastAPI + Lambda agents) to EC2 with Nginx reverse proxy.

## Architecture
- **EC2 Instance**: Ubuntu 22.04 LTS (t3.small/t3.medium recommended)
- **Nginx**: Reverse proxy serving Angular frontend + proxying API to FastAPI
- **Angular**: Built production files served as static content
- **Backend**: Full FastAPI app.py running on EC2 (all business logic)
- **Lambda functions**: Market data & AI agents (already deployed, optional)
- **No API Gateway needed**: Direct backend on EC2, can call Lambda functions for heavy processing

---

## Prerequisites Checklist

### AWS Permissions Required
- [x] Lambda (already have - functions deployed)
- [ ] EC2:DescribeImages
- [ ] EC2:DescribeInstances
- [ ] EC2:RunInstances
- [ ] EC2:CreateSecurityGroup
- [ ] EC2:AuthorizeSecurityGroupIngress
- [ ] EC2:CreateKeyPair
- [ ] EC2:DescribeKeyPairs

### Test Your EC2 Permissions
```bash
# Open NEW PowerShell terminal (for AWS CLI to be in PATH)
# Or restart current terminal

# 1. Verify AWS identity
aws sts get-caller-identity

# 2. Test EC2 read permissions
aws ec2 describe-instances --region us-east-1

# 3. Test AMI list (Amazon Linux 2)
aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" --query 'Images[0:3].[ImageId,Name,CreationDate]' --output table --region us-east-1

# 4. Check existing key pairs
aws ec2 describe-key-pairs --region us-east-1

# 5. Check existing security groups
aws ec2 describe-security-groups --region us-east-1
```

---

## Step 1: Create EC2 Key Pair

### Option A: AWS Console (Recommended for First Time)
1. Go to **EC2 Console** → **Key Pairs** → **Create key pair**
2. Name: `jbac-trading-coach-key`
3. Type: RSA
4. Format: `.pem` (for SSH)
5. **Download** the .pem file → Save to safe location (you'll need it for SSH)

### Option B: AWS CLI
```bash
# Create key pair and save to file
aws ec2 create-key-pair --key-name jbac-trading-coach-key --query 'KeyMaterial' --output text --region us-east-1 > jbac-trading-coach-key.pem

# Set proper permissions (Git Bash on Windows)
chmod 400 jbac-trading-coach-key.pem
```

---

## Step 2: Create Security Group

```bash
# 1. Create security group
aws ec2 create-security-group \
  --group-name jbac-trading-coach-sg \
  --description "Security group for JBAC Trading Coach EC2" \
  --region us-east-1

# Note the GroupId from output (e.g., sg-0123456789abcdef0)

# 2. Add SSH rule (port 22) - IMPORTANT: Replace YOUR_IP with your actual IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32 \
  --region us-east-1

# 3. Add HTTP rule (port 80) - public access
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region us-east-1

# 4. Add HTTPS rule (port 443) - for future SSL
aws ec2 authorize-security-group-ingress \
  --group-id sg-XXXXXXXXX \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region us-east-1
```

**Get Your IP**: Visit https://whatismyipaddress.com/ or run:
```bash
curl ifconfig.me
```

---

## Step 3: Launch EC2 Instance

### Recommended Instance Configuration
- **AMI**: Ubuntu 22.04 LTS (`ami-0c7217cdde317cfec` in us-east-1)
- **Instance Type**: 
  - **t3.small** (2 vCPU, 2 GB RAM) - $0.0208/hour (~$15/month) - **Recommended for production**
  - t3.medium (2 vCPU, 4 GB RAM) - $0.0416/hour (~$30/month) - If you need more headroom
  - t2.micro (1 vCPU, 1 GB RAM) - FREE tier, but may be tight with full app.py
- **Storage**: 20 GB gp3 SSD
- **Region**: us-east-1 (same as DynamoDB/Bedrock)

### Launch Command
```bash
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name jbac-trading-coach-key \
  --security-group-ids sg-XXXXXXXXX \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=JBAC-Trading-Coach}]' \
  --region us-east-1
```

**Note the InstanceId** from output (e.g., `i-0123456789abcdef0`)  i-0d70081efc540c87f

### Check Instance Status
```bash
aws ec2 describe-instances \
  --instance-ids i-XXXXXXXXX \
  --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,PrivateIpAddress]' \
  --output table \
  --region us-east-1
```

Wait for state to be `running` and note the **Public IP Address**.

---

## Step 4: Connect to EC2 Instance

### SSH Connection
```bash
# From Git Bash on Windows (or PowerShell with OpenSSH)
ssh -i path/to/jbac-trading-coach-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Example:
# ssh -i C:/Users/YourName/.ssh/jbac-trading-coach-key.pem ubuntu@3.88.123.45
```

---

## Step 5: Install Dependencies on EC2

Once connected via SSH, run these commands:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Node.js 18 (for Angular build if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Install Nginx
sudo apt install -y nginx

# 4. Install Python 3.11 (for backend if needed later)
sudo apt install -y python3.11 python3.11-venv python3-pip

# 5. Install AWS CLI (for Lambda invoke)
sudo apt install -y awscli

# 6. Verify installations
node --version
npm --version
nginx -v
python3.11 --version
aws --version
```

---

## Step 6: Build Angular Frontend (From Your Windows Machine)

```powershell
# Navigate to UI folder
cd c:\Users\Jai Ansh Bindra\JBAC_AI_Trading_Coach\ui

# Install dependencies if not done
npm install

# Build for production with EC2 backend URL
# First, update environment.prod.ts with Lambda URLs
```

Create/update `ui/src/environments/environment.prod.ts`:
```typescript
export const environment = {
  production: true,
  apiUrl: 'http://YOUR_EC2_PUBLIC_IP/api',
  googleClientId: 'YOUR_GOOGLE_CLIENT_ID'
};
```

```powershell
# Build production bundle
npm run build

# This creates ui/dist/ui/ folder with compiled files
```

---

## Step 7: Upload Frontend Files to EC2

### Option A: Using SCP (Recommended)
```bash
# From Git Bash or PowerShell with OpenSSH
scp -i path/to/jbac-trading-coach-key.pem -r ui/dist/ui/* ubuntu@YOUR_EC2_PUBLIC_IP:/tmp/ui-build/

# Example:
# scp -i C:/Users/YourName/.ssh/jbac-trading-coach-key.pem -r ui/dist/ui/* ubuntu@3.88.123.45:/tmp/ui-build/
```

### Option B: Git Clone (If repo is public or you add deploy key)
```bash
# On EC2 instance
cd /home/ubuntu
git clone https://github.com/JaiAnshSB26/JBAC_AI_Trading_Coach.git
cd JBAC_AI_Trading_Coach/ui
npm install
npm run build
```

---

## Step 8: Configure Nginx

SSH into EC2 and create Nginx config:

```bash
# Create Nginx site configuration
sudo nano /etc/nginx/sites-available/jbac-trading-coach
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_EC2_PUBLIC_IP;  # Replace with your EC2 IP or domain

    # Frontend - Angular static files
    root /var/www/jbac-trading-coach;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend routes (Angular routing)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to Lambda (via backend FastAPI on same EC2 or direct Lambda)
    location /api/ {
        # Option 1: Proxy to Lambda function URL (if using Lambda URL)
        # proxy_pass https://YOUR_LAMBDA_FUNCTION_URL/;
        
        # Option 2: Proxy to local FastAPI that invokes Lambda
        proxy_pass http://127.0.0.1:8000/;
        
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/jbac-trading-coach /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Step 9: Deploy Frontend Files

```bash
# Create web root directory
sudo mkdir -p /var/www/jbac-trading-coach

# Copy built files (if uploaded to /tmp)
sudo cp -r /tmp/ui-build/* /var/www/jbac-trading-coach/

# Or if using git clone method
# sudo cp -r /home/ubuntu/JBAC_AI_Trading_Coach/ui/dist/ui/* /var/www/jbac-trading-coach/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/jbac-trading-coach
sudo chmod -R 755 /var/www/jbac-trading-coach

# Verify files
ls -la /var/www/jbac-trading-coach
```

---

## Step 10: Test the Deployment

### 1. Test Nginx
```bash
curl http://YOUR_EC2_PUBLIC_IP
# Should return Angular index.html
```

### 2. Access from Browser
Open browser: `http://YOUR_EC2_PUBLIC_IP`

### 3. Check Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Step 11: Update Lambda CORS (CRITICAL)

Your Lambda functions need to allow requests from EC2 IP:

```bash
# Update each Lambda function's CORS_ORIGINS environment variable
aws lambda update-function-configuration \
  --function-name jbac-trading-coach-api \
  --environment Variables='{
    "CORS_ORIGINS":"http://YOUR_EC2_PUBLIC_IP,http://localhost:4200",
    "GOOGLE_CLIENT_ID":"YOUR_GOOGLE_CLIENT_ID",
    "BEDROCK_MODEL_ID":"anthropic.claude-3-5-sonnet-20241022-v2:0",
    "DYNAMODB_REGION":"us-east-1",
    "USERS_TABLE":"Users",
    "PORTFOLIOS_TABLE":"Portfolios",
    "TRADES_TABLE":"Trades",
    "JWT_ALGORITHM":"HS256"
  }' \
  --region us-east-1
```

---

## Architecture Diagrams

### Without API Gateway (Current Plan)
```
User Browser
    ↓ HTTP
EC2 (Nginx)
    ├→ Static Files (Angular) → Served directly
    └→ /api/* → FastAPI on EC2:8000 → boto3.client('lambda').invoke() → Lambda Functions
```

### With API Gateway (Alternative)
```
User Browser
    ↓ HTTP
EC2 (Nginx)
    ├→ Static Files (Angular) → Served directly
    └→ /api/* → API Gateway REST API → Lambda Functions
```

---

## REQUIRED: Run FastAPI Backend on EC2

Your full app.py runs on EC2 with all business logic:

```bash
# On EC2 instance
cd /home/ubuntu/JBAC_AI_Trading_Coach

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-ec2.txt

# Create .env file
nano .env
```

Add to `.env`:
```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_REGION=us-east-1

# DynamoDB Tables
USERS_TABLE=Users
PORTFOLIOS_TABLE=Portfolios
TRADES_TABLE=Trades

# Google OAuth
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# JWT Secret (generate a secure random string)
JWT_SECRET=your-super-secret-jwt-key-change-this

# Storage (use DynamoDB in production)
USE_LOCAL_STORAGE=false

# CORS (update with your EC2 IP)
CORS_ORIGINS=http://YOUR_EC2_IP,http://localhost:4200

# API Prefix
API_PREFIX=/api

# Logging
LOG_LEVEL=INFO
```

```bash
# Run FastAPI with Uvicorn
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 2

# Or use systemd service for production (see next section)
```

---

## Production: FastAPI Systemd Service

Create `/etc/systemd/system/jbac-backend.service`:

```ini
[Unit]
Description=JBAC Trading Coach FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/JBAC_AI_Trading_Coach
Environment="PATH=/home/ubuntu/JBAC_AI_Trading_Coach/venv/bin"
Environment="AWS_DEFAULT_REGION=us-east-1"
Environment="GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID"
Environment="BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0"
Environment="DYNAMODB_REGION=us-east-1"
Environment="USERS_TABLE=Users"
Environment="PORTFOLIOS_TABLE=Portfolios"
Environment="TRADES_TABLE=Trades"
ExecStart=/home/ubuntu/JBAC_AI_Trading_Coach/venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable jbac-backend
sudo systemctl start jbac-backend
sudo systemctl status jbac-backend
```

---

## Monitoring & Maintenance

### Check Service Status
```bash
# Nginx
sudo systemctl status nginx
sudo nginx -t  # Test config

# FastAPI (if using systemd)
sudo systemctl status jbac-backend
journalctl -u jbac-backend -f  # Follow logs

# Disk space
df -h

# Memory usage
free -h
```

### Update Deployment
```bash
# Update frontend
cd /home/ubuntu/JBAC_AI_Trading_Coach
git pull
cd ui
npm install
npm run build
sudo cp -r dist/ui/* /var/www/jbac-trading-coach/
sudo systemctl reload nginx

# Update backend
cd /home/ubuntu/JBAC_AI_Trading_Coach
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart jbac-backend
```

---

## Cost Estimation

**Monthly costs (24/7 operation):**
- EC2 t3.small: ~$15/month (**Recommended**)
- EC2 t3.medium: ~$30/month (if you need more power)
- EC2 t2.micro: **FREE** (first 12 months, 750 hours/month)
- EBS Storage (20 GB): ~$2/month
- Data Transfer: ~$5-10/month (first 100 GB free)
- DynamoDB: **FREE** tier (25 GB storage, 25 WCU/RCU)
- Bedrock: ~$0.10-2/month (pay per use)

**Total: $0-5/month** (Year 1 with free tier)  
**Total: ~$20-35/month** (After year 1 with t3.small)

---

## Troubleshooting

### 1. Can't SSH to EC2
- Check security group allows port 22 from your IP
- Verify .pem file permissions: `chmod 400 key.pem`
- Check instance is running: `aws ec2 describe-instances`

### 2. Nginx 502 Bad Gateway
- Check FastAPI is running: `curl http://127.0.0.1:8000/health`
- Check systemd service: `sudo systemctl status jbac-backend`
- Check logs: `sudo tail -f /var/log/nginx/error.log`

### 3. CORS Errors in Browser
- Update Lambda CORS_ORIGINS with EC2 IP
- Check Nginx proxy headers are set
- Clear browser cache

### 4. Lambda Invoke Errors
- Verify IAM role has lambda:InvokeFunction permission
- Check Lambda function names match in code
- Check AWS credentials configured on EC2

---

## Next Steps After EC2 Deployment

1. **Custom Domain** (Optional)
   - Register domain (e.g., tradingcoach.yourdomain.com)
   - Point DNS A record to EC2 IP
   - Update Nginx `server_name` to domain
   - Install SSL certificate (Let's Encrypt)

2. **HTTPS Setup**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d tradingcoach.yourdomain.com
   ```

3. **Monitoring**
   - CloudWatch for Lambda metrics
   - EC2 CloudWatch agent for instance metrics
   - Application logging (Sentry, LogRocket, etc.)

4. **Backups**
   - EC2 AMI snapshots
   - DynamoDB point-in-time recovery (already enabled)

5. **CI/CD** (Optional)
   - GitHub Actions to auto-deploy on push
   - AWS CodeDeploy integration

---

## Security Checklist

- [ ] SSH key stored securely (not in repo)
- [ ] Security group restricts SSH to your IP only
- [ ] HTTPS enabled (if using custom domain)
- [ ] Environment variables not hardcoded
- [ ] IAM roles follow least privilege
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Nginx security headers configured
- [ ] Lambda CORS restricted to EC2 IP (not *)

---

## Support Commands Reference

```bash
# AWS
aws sts get-caller-identity                           # Check AWS identity
aws ec2 describe-instances --region us-east-1        # List EC2 instances
aws lambda list-functions --region us-east-1         # List Lambda functions

# Nginx
sudo nginx -t                                         # Test config
sudo systemctl restart nginx                         # Restart
sudo tail -f /var/log/nginx/error.log               # View errors

# SystemD (FastAPI)
sudo systemctl status jbac-backend                   # Check status
sudo systemctl restart jbac-backend                  # Restart
journalctl -u jbac-backend -f                       # Follow logs

# Network
curl http://localhost                                # Test Nginx locally
curl http://localhost:8000/health                   # Test FastAPI locally
netstat -tlnp | grep :80                           # Check port 80 listener
```

---

**Ready to proceed?** Start with testing your EC2 permissions (Step 0), then move through each step sequentially!
