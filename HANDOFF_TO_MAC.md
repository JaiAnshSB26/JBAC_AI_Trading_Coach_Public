# 🤝 EC2 Deployment Handoff - For Mac User

## 📋 Current Status

### ✅ What's Already Done:
- **EC2 Instance**: Running `t3.small` (2 vCPU, 2 GB RAM)
  - Instance ID: `i-056facf44eb423edb`
  - Public IP: **`44.220.130.180`**
  - Region: `us-east-1`
  - Status: `running`
  
- **Security Group**: `jbac-trading-coach-sg` (`sg-095b0d6c5eaea4e62`)
  - SSH (port 22): From IP `129.104.65.6` only
  - HTTP (port 80): Public access
  - HTTPS (port 443): Public access

- **AWS Resources**:
  - Lambda functions: `jbac-market-data`, `jbac-llm-agents` (deployed)
  - DynamoDB tables: Users, Portfolios, Trades (ACTIVE)
  - Google OAuth: `YOUR_GOOGLE_CLIENT_ID` (configure your own in Google Cloud Console)

### ⚠️ What Needs to Be Done:
- **SSH key issue**: Need to recreate the key pair to connect to EC2
- Install all dependencies on EC2 (Nginx, Python, Node.js)
- Deploy backend (FastAPI)
- Deploy frontend (Angular)
- Configure systemd service

---

## 🔑 Step 1: Get SSH Access

The EC2 instance exists but we need a new SSH key. Here's what to do:

### Option A: AWS Console (Recommended - 5 min)

1. **Go to AWS Console**: https://console.aws.amazon.com/ec2/
   - Make sure region is **N. Virginia (us-east-1)**

2. **Update Security Group for Your Mac's IP**:
   - Left sidebar → **Security Groups**
   - Find `jbac-trading-coach-sg`
   - Click **Edit inbound rules**
   - Find the SSH rule (port 22)
   - Change source to **My IP** (it will auto-detect your Mac's IP)
   - Save

3. **Create New Key Pair**:
   - Left sidebar → **Key Pairs**
   - Select existing `jbac-trading-coach-key` → **Actions** → **Delete**
   - Click **Create key pair**
   - Name: `jbac-trading-coach-key`
   - Type: RSA
   - Format: `.pem`
   - Click **Create** → Save to `~/Downloads/jbac-trading-coach-key.pem`

4. **Set Permissions & Connect**:
   ```bash
   # Move key to secure location
   mv ~/Downloads/jbac-trading-coach-key.pem ~/.ssh/
   
   # Set proper permissions
   chmod 400 ~/.ssh/jbac-trading-coach-key.pem
   
   # Connect to EC2
   ssh -i ~/.ssh/jbac-trading-coach-key.pem ubuntu@44.220.130.180
   ```

### Option B: AWS CLI (Faster - 2 min)

```bash
# Install AWS CLI on Mac (if not installed)
brew install awscli

# Configure AWS credentials
aws configure
# Enter:
# - AWS Access Key ID: (get from Windows user)
# - AWS Secret Access Key: (get from Windows user)
# - Region: us-east-1
# - Output format: json

# Get your Mac's public IP
MY_IP=$(curl -s https://api.ipify.org)
echo "Your IP: $MY_IP"

# Update security group to allow SSH from your Mac
aws ec2 revoke-security-group-ingress \
  --group-id sg-095b0d6c5eaea4e62 \
  --protocol tcp \
  --port 22 \
  --cidr 129.104.65.6/32 \
  --region us-east-1

aws ec2 authorize-security-group-ingress \
  --group-id sg-095b0d6c5eaea4e62 \
  --protocol tcp \
  --port 22 \
  --cidr ${MY_IP}/32 \
  --region us-east-1

# Delete old key pair
aws ec2 delete-key-pair \
  --key-name jbac-trading-coach-key \
  --region us-east-1

# Create new key pair
aws ec2 create-key-pair \
  --key-name jbac-trading-coach-key \
  --query 'KeyMaterial' \
  --output text \
  --region us-east-1 > ~/.ssh/jbac-trading-coach-key.pem

# Set permissions
chmod 400 ~/.ssh/jbac-trading-coach-key.pem

# Connect
ssh -i ~/.ssh/jbac-trading-coach-key.pem ubuntu@44.220.130.180
```

---

## 🛠️ Step 2: Install Dependencies on EC2

Once connected via SSH, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18 (for Angular build)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install AWS CLI
sudo apt install -y awscli

# Install Git
sudo apt install -y git

# Verify installations
node --version
npm --version
nginx -v
python3.11 --version
aws --version
git --version
```

---

## 📦 Step 3: Clone Repository & Setup Backend

```bash
# Clone the repo
cd /home/ubuntu
git clone https://github.com/JaiAnshSB26/JBAC_AI_Trading_Coach.git
cd JBAC_AI_Trading_Coach

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements-ec2.txt

# Configure AWS credentials on EC2
aws configure
# Enter the same AWS credentials as before
# Region: us-east-1
```

---

## 🔐 Step 4: Create .env File

```bash
# Create backend .env file
nano backend/.env
```

Paste this content (ask Windows user for these values):
```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY

# DynamoDB Tables
USERS_TABLE=Users
PORTFOLIOS_TABLE=Portfolios
TRADES_TABLE=Trades

# Google OAuth
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-change-this

# Storage
USE_LOCAL_STORAGE=false

# CORS (update with EC2 IP)
CORS_ORIGINS=http://44.220.130.180,http://localhost:4200

# API Prefix
API_PREFIX=/api

# Logging
LOG_LEVEL=INFO
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🌐 Step 5: Build Angular Frontend (on your Mac)

```bash
# On your Mac (not EC2)
cd ~/path/to/JBAC_AI_Trading_Coach/ui

# Install dependencies
npm install

# Update environment for production
nano src/environments/environment.prod.ts
```

Update to:
```typescript
export const environment = {
  production: true,
  apiUrl: 'http://YOUR_EC2_IP_OR_DOMAIN/api',
  googleClientId: 'YOUR_GOOGLE_CLIENT_ID'
};
```

```bash
# Build production bundle
npm run build

# Upload to EC2
scp -i ~/.ssh/jbac-trading-coach-key.pem -r dist/ui/* ubuntu@44.220.130.180:/tmp/ui-build/
```

---

## ⚙️ Step 6: Configure Nginx (on EC2)

```bash
# SSH back into EC2
ssh -i ~/.ssh/jbac-trading-coach-key.pem ubuntu@44.220.130.180

# Create Nginx config
sudo nano /etc/nginx/sites-available/jbac-trading-coach
```

Paste this:
```nginx
server {
    listen 80;
    server_name 44.220.130.180;

    root /var/www/jbac-trading-coach;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Save and enable:
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/jbac-trading-coach /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Deploy frontend files
sudo mkdir -p /var/www/jbac-trading-coach
sudo cp -r /tmp/ui-build/* /var/www/jbac-trading-coach/
sudo chown -R www-data:www-data /var/www/jbac-trading-coach
sudo chmod -R 755 /var/www/jbac-trading-coach

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 🚀 Step 7: Setup FastAPI Systemd Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/jbac-backend.service
```

Paste:
```ini
[Unit]
Description=JBAC Trading Coach FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/JBAC_AI_Trading_Coach
Environment="PATH=/home/ubuntu/JBAC_AI_Trading_Coach/venv/bin"
EnvironmentFile=/home/ubuntu/JBAC_AI_Trading_Coach/backend/.env
ExecStart=/home/ubuntu/JBAC_AI_Trading_Coach/venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jbac-backend
sudo systemctl start jbac-backend
sudo systemctl status jbac-backend
```

---

## ✅ Step 8: Test Everything

```bash
# Test backend
curl http://127.0.0.1:8000/api/health

# Test Nginx
curl http://44.220.130.180

# Check logs
sudo tail -f /var/log/nginx/access.log
journalctl -u jbac-backend -f
```

**In browser**: http://44.220.130.180

---

## 📝 AWS Credentials You Need

You will need to configure:
1. **AWS Access Key ID**: Create IAM user with appropriate permissions
2. **AWS Secret Access Key**: From the IAM user you create
3. **JWT Secret**: Generate a secure random string
4. **Google OAuth Client ID**: Create in Google Cloud Console

---

## 🐛 Troubleshooting

### Can't SSH
```bash
# Check instance is running
aws ec2 describe-instances \
  --instance-ids i-056facf44eb423edb \
  --query 'Reservations[0].Instances[0].State.Name' \
  --region us-east-1

# Check security group allows your IP
aws ec2 describe-security-groups \
  --group-ids sg-095b0d6c5eaea4e62 \
  --region us-east-1
```

### Backend not starting
```bash
# Check logs
journalctl -u jbac-backend -n 50

# Test manually
cd /home/ubuntu/JBAC_AI_Trading_Coach
source venv/bin/activate
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

### Nginx 502 error
```bash
# Check backend is running
curl http://127.0.0.1:8000/api/health

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 Cost Reminder

- **EC2 t3.small**: ~$15/month (24/7)
- **EBS Storage**: ~$2/month
- **DynamoDB**: FREE tier
- **Bedrock API**: Pay per use (~$0.10-2/month)

**Total**: ~$17-20/month

---

## 🎯 Quick Commands Reference

```bash
# SSH into EC2
ssh -i ~/.ssh/jbac-trading-coach-key.pem ubuntu@44.220.130.180

# Restart backend
sudo systemctl restart jbac-backend

# View backend logs
journalctl -u jbac-backend -f

# Restart Nginx
sudo systemctl restart nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log

# Update code
cd /home/ubuntu/JBAC_AI_Trading_Coach
git pull
source venv/bin/activate
pip install -r requirements-ec2.txt
sudo systemctl restart jbac-backend
```

---

## 📞 Contact

If you get stuck, the previous Windows user can help with:
- AWS credentials
- Google OAuth configuration
- DynamoDB table details
- Lambda function names

---

Good luck! 🚀
