# JBAC Trading Coach - Maintenance Guide

## Quick Reference for Managing Your Deployed Application

**Domain**: https://trading.jbac.dev  
**EC2 Instance**: i-0691cfc2dcb5375ba (54.167.23.220)  
**Region**: us-east-1

---

## 🔧 Common Operations

### SSH into EC2
```bash
# From Git Bash on Windows
ssh -i jbac-trading-coach-key.pem ubuntu@54.167.23.220

# Or use the domain
ssh -i jbac-trading-coach-key.pem ubuntu@trading.jbac.dev
```

### Exit SSH
```bash
exit
# Or press Ctrl+D
```

---

## 🎛️ Backend (FastAPI) Management

### Check Status
```bash
sudo systemctl status jbac-backend
```

### Start Backend
```bash
sudo systemctl start jbac-backend
```

### Stop Backend
```bash
sudo systemctl stop jbac-backend
```

### Restart Backend
```bash
sudo systemctl restart jbac-backend
```

### Enable on Boot (Auto-start)
```bash
sudo systemctl enable jbac-backend
```

### Disable Auto-start
```bash
sudo systemctl disable jbac-backend
```

### View Backend Logs (Live)
```bash
# Follow logs in real-time
sudo journalctl -u jbac-backend -f

# View last 50 lines
sudo journalctl -u jbac-backend -n 50

# View last 100 lines
sudo journalctl -u jbac-backend -n 100

# Press 'q' to quit log viewer
```

### Test Backend Directly
```bash
# Test health endpoint locally
curl http://127.0.0.1:8000/api/health

# Test via domain
curl https://trading.jbac.dev/api/health
```

---

## 🌐 Frontend (Nginx) Management

### Check Status
```bash
sudo systemctl status nginx
```

### Start Nginx
```bash
sudo systemctl start nginx
```

### Stop Nginx
```bash
sudo systemctl stop nginx
```

### Restart Nginx
```bash
sudo systemctl restart nginx
```

### Reload Nginx (Graceful restart, no downtime)
```bash
sudo systemctl reload nginx
```

### Test Nginx Configuration
```bash
# Check for syntax errors before restarting
sudo nginx -t
```

### View Nginx Logs
```bash
# Access logs (who visited)
sudo tail -f /var/log/nginx/access.log

# Error logs (problems)
sudo tail -f /var/log/nginx/error.log

# Last 50 lines of error log
sudo tail -n 50 /var/log/nginx/error.log

# Press Ctrl+C to stop following logs
```

---

## 📊 System Monitoring

### Check Disk Space
```bash
df -h
# Look for /dev/root usage
```

### Check Memory Usage
```bash
free -h
```

### Check CPU and Process Usage
```bash
top
# Press 'q' to quit

# Or use htop (more user-friendly)
htop
# Press 'q' to quit
```

### Check Which Services Are Running
```bash
systemctl list-units --type=service --state=running
```

### Check Network Connections
```bash
# See what's listening on ports
sudo netstat -tlnp

# Check port 80 (HTTP)
sudo netstat -tlnp | grep :80

# Check port 443 (HTTPS)
sudo netstat -tlnp | grep :443

# Check port 8000 (Backend)
sudo netstat -tlnp | grep :8000
```

---

## 🔄 Update/Deploy Changes

### Update Backend Code
```bash
# SSH into EC2
ssh -i jbac-trading-coach-key.pem ubuntu@54.167.23.220

# Navigate to project
cd /home/ubuntu/JBAC_AI_Trading_Coach

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements-ec2.txt

# Restart backend service
sudo systemctl restart jbac-backend

# Check status
sudo systemctl status jbac-backend
```

### Update Frontend Code

**Step 1: Build on Windows**
```powershell
# On your Windows machine
cd C:\Users\Jai Ansh Bindra\JBAC_AI_Trading_Coach\ui

# Pull latest code
git pull origin main

# Install dependencies if package.json changed
npm install

# Build production bundle
npm run build
```

**Step 2: Upload to EC2**
```bash
# From Git Bash on Windows
scp -i jbac-trading-coach-key.pem -r ui/dist/ui/* ubuntu@54.167.23.220:/tmp/ui-build/
```

**Step 3: Deploy on EC2**
```bash
# SSH into EC2
ssh -i jbac-trading-coach-key.pem ubuntu@54.167.23.220

# Copy files to web root
sudo cp -r /tmp/ui-build/* /var/www/jbac-trading-coach/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/jbac-trading-coach
sudo chmod -R 755 /var/www/jbac-trading-coach

# Reload Nginx (no downtime)
sudo systemctl reload nginx
```

---

## 🔐 SSL Certificate Renewal

Let's Encrypt certificates expire every 90 days, but Certbot auto-renews them.

### Check Certificate Expiry
```bash
sudo certbot certificates
```

### Test Auto-Renewal
```bash
sudo certbot renew --dry-run
```

### Manually Renew (if needed)
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 🛠️ Troubleshooting

### Backend Not Responding
```bash
# 1. Check status
sudo systemctl status jbac-backend

# 2. Check logs for errors
sudo journalctl -u jbac-backend -n 100

# 3. Test locally
curl http://127.0.0.1:8000/api/health

# 4. Restart
sudo systemctl restart jbac-backend
```

### Frontend Shows Old Version
```bash
# 1. Clear browser cache (Ctrl+Shift+R or Ctrl+F5)

# 2. Check files on server
ls -la /var/www/jbac-trading-coach/

# 3. Redeploy frontend (see Update Frontend Code above)

# 4. Reload Nginx
sudo systemctl reload nginx
```

### Site Not Accessible (502 Bad Gateway)
```bash
# 1. Check if backend is running
sudo systemctl status jbac-backend

# 2. Check Nginx is running
sudo systemctl status nginx

# 3. Check Nginx config
sudo nginx -t

# 4. Check Nginx error logs
sudo tail -n 50 /var/log/nginx/error.log

# 5. Restart both
sudo systemctl restart jbac-backend
sudo systemctl restart nginx
```

### CORS Errors in Browser
```bash
# 1. Check backend .env file
cat /home/ubuntu/JBAC_AI_Trading_Coach/backend/.env | grep CORS

# 2. Should show:
# CORS_ORIGINS=https://trading.jbac.dev,http://54.167.23.220,http://localhost:4200

# 3. If wrong, edit:
nano /home/ubuntu/JBAC_AI_Trading_Coach/backend/.env

# 4. Restart backend
sudo systemctl restart jbac-backend
```

### Out of Disk Space
```bash
# 1. Check disk usage
df -h

# 2. Find large files
sudo du -h /var/log/ | sort -h | tail -20

# 3. Clean old logs
sudo journalctl --vacuum-time=7d

# 4. Clean apt cache
sudo apt clean
```

---

## 📝 Configuration File Locations

### Backend
- **App Code**: `/home/ubuntu/JBAC_AI_Trading_Coach/backend/`
- **Environment Variables**: `/home/ubuntu/JBAC_AI_Trading_Coach/backend/.env`
- **Systemd Service**: `/etc/systemd/system/jbac-backend.service`
- **Virtual Environment**: `/home/ubuntu/JBAC_AI_Trading_Coach/venv/`

### Frontend
- **Static Files**: `/var/www/jbac-trading-coach/`
- **Nginx Config**: `/etc/nginx/sites-available/jbac-trading-coach`
- **Nginx Logs**: `/var/log/nginx/`

### SSL Certificates
- **Certificates**: `/etc/letsencrypt/live/trading.jbac.dev/`
- **Certbot Config**: `/etc/letsencrypt/`

---

## 🚨 Emergency Commands

### Reboot EC2 Instance
```bash
sudo reboot
# Wait 2-3 minutes, then SSH back in
```

### Stop All Services
```bash
sudo systemctl stop jbac-backend
sudo systemctl stop nginx
```

### Start All Services
```bash
sudo systemctl start nginx
sudo systemctl start jbac-backend
```

### Check All Service Status at Once
```bash
sudo systemctl status nginx jbac-backend
```

---

## 📞 Health Check Commands (Quick Diagnostics)

Run these to verify everything is working:

```bash
# 1. Check backend health
curl http://127.0.0.1:8000/api/health

# 2. Check external access
curl https://trading.jbac.dev/api/health

# 3. Check services
sudo systemctl status nginx jbac-backend

# 4. Check disk space
df -h

# 5. Check memory
free -h

# 6. Check recent errors
sudo journalctl -u jbac-backend -n 20
sudo tail -n 20 /var/log/nginx/error.log
```

---

## 🔗 Important URLs

- **Live Site**: https://trading.jbac.dev
- **Backend Health**: https://trading.jbac.dev/api/health
- **Google OAuth Console**: https://console.cloud.google.com/apis/credentials
- **AWS Console**: https://console.aws.amazon.com/
- **EC2 Instances**: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances

---

## 💰 Cost Monitoring

### Check AWS Costs
1. Go to: https://console.aws.amazon.com/billing/
2. View "Bills" for current month
3. Monitor:
   - EC2 t3.small: ~$15/month
   - EBS Storage: ~$2/month
   - Data Transfer: varies
   - DynamoDB: Free tier
   - Bedrock: Pay per use

### Reduce Costs (if needed)
```bash
# Stop instance when not in use (loses public IP!)
aws ec2 stop-instances --instance-ids i-0691cfc2dcb5375ba --region us-east-1

# Start instance
aws ec2 start-instances --instance-ids i-0691cfc2dcb5375ba --region us-east-1

# Downgrade to t3.micro (cheaper but less powerful)
# Must stop instance first, then change instance type in AWS Console
```

---

## 📚 Additional Resources

- **EC2 Deployment Guide**: See `EC2_DEPLOYMENT.md`
- **Backend Code**: `/home/ubuntu/JBAC_AI_Trading_Coach/backend/app.py`
- **Frontend Code**: `ui/src/`
- **Requirements**: `requirements-ec2.txt`

---

**Need help?** Check logs first, then restart services. Most issues are solved by:
1. Check logs: `sudo journalctl -u jbac-backend -n 50`
2. Restart backend: `sudo systemctl restart jbac-backend`
3. Restart Nginx: `sudo systemctl restart nginx`

**Still stuck?** Check the troubleshooting section above! 🚀
