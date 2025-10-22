# EC2 Deployment Script for JBAC Trading Coach
# Run this script step-by-step to deploy to AWS EC2

Write-Host "=== JBAC Trading Coach EC2 Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REGION = "us-east-1"
$KEY_NAME = "jbac-trading-coach-key"
$SECURITY_GROUP_NAME = "jbac-trading-coach-sg"
$INSTANCE_NAME = "JBAC-Trading-Coach"
$UBUNTU_AMI = "ami-0c398cb65a93047f2"  # Ubuntu 22.04 LTS (latest as of Oct 2025)
$INSTANCE_TYPE = "t3.small"  # $15/month - change to t2.micro for free tier

Write-Host "Step 1: Get your public IP for SSH security" -ForegroundColor Yellow
$MY_IP = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content
Write-Host "Your IP: $MY_IP" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Creating EC2 Key Pair..." -ForegroundColor Yellow
Write-Host "Command to run:" -ForegroundColor Cyan
Write-Host "aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text --region $REGION > ${KEY_NAME}.pem" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to create the key pair (or Ctrl+C to skip if already exists)..." -ForegroundColor Magenta
Read-Host

try {
    aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text --region $REGION | Out-File -FilePath "${KEY_NAME}.pem" -Encoding ASCII
    Write-Host "✓ Key pair created and saved to ${KEY_NAME}.pem" -ForegroundColor Green
    Write-Host "IMPORTANT: Save this file in a secure location!" -ForegroundColor Red
} catch {
    Write-Host "Key pair may already exist or error occurred. Check AWS console." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 3: Creating Security Group..." -ForegroundColor Yellow
Write-Host "Command to run:" -ForegroundColor Cyan
Write-Host "aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description 'Security group for JBAC Trading Coach' --region $REGION" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to create security group..." -ForegroundColor Magenta
Read-Host

try {
    $SG_OUTPUT = aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description "Security group for JBAC Trading Coach" --region $REGION | ConvertFrom-Json
    $SG_ID = $SG_OUTPUT.GroupId
    Write-Host "✓ Security group created: $SG_ID" -ForegroundColor Green
    
    # Add SSH rule
    Write-Host "Adding SSH rule (port 22) for your IP..." -ForegroundColor Yellow
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr "${MY_IP}/32" --region $REGION
    Write-Host "✓ SSH access allowed from $MY_IP" -ForegroundColor Green
    
    # Add HTTP rule
    Write-Host "Adding HTTP rule (port 80)..." -ForegroundColor Yellow
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr "0.0.0.0/0" --region $REGION
    Write-Host "✓ HTTP access allowed from anywhere" -ForegroundColor Green
    
    # Add HTTPS rule
    Write-Host "Adding HTTPS rule (port 443)..." -ForegroundColor Yellow
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr "0.0.0.0/0" --region $REGION
    Write-Host "✓ HTTPS access allowed from anywhere" -ForegroundColor Green
    
} catch {
    Write-Host "Security group may already exist. Fetching existing group ID..." -ForegroundColor Yellow
    $SG_OUTPUT = aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME --region $REGION | ConvertFrom-Json
    $SG_ID = $SG_OUTPUT.SecurityGroups[0].GroupId
    Write-Host "Using existing security group: $SG_ID" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 4: Launching EC2 Instance..." -ForegroundColor Yellow
Write-Host "Instance Type: $INSTANCE_TYPE" -ForegroundColor Cyan
Write-Host "AMI: $UBUNTU_AMI (Ubuntu 22.04 LTS)" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will cost approximately:" -ForegroundColor Red
Write-Host "  - t3.small: ~`$15/month" -ForegroundColor Yellow
Write-Host "  - t2.micro: FREE (first 12 months)" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to launch instance (or Ctrl+C to cancel)..." -ForegroundColor Magenta
Read-Host

$INSTANCE_OUTPUT = aws ec2 run-instances `
    --image-id $UBUNTU_AMI `
    --instance-type $INSTANCE_TYPE `
    --key-name $KEY_NAME `
    --security-group-ids $SG_ID `
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" `
    --region $REGION | ConvertFrom-Json

$INSTANCE_ID = $INSTANCE_OUTPUT.Instances[0].InstanceId
Write-Host "✓ EC2 Instance launched: $INSTANCE_ID" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Waiting for instance to start..." -ForegroundColor Yellow
Write-Host "This may take 1-2 minutes..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

$INSTANCE_INFO = $null
$retries = 0
while ($retries -lt 12) {
    try {
        $INSTANCE_INFO = aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION | ConvertFrom-Json
        $STATE = $INSTANCE_INFO.Reservations[0].Instances[0].State.Name
        $PUBLIC_IP = $INSTANCE_INFO.Reservations[0].Instances[0].PublicIpAddress
        
        if ($STATE -eq "running" -and $PUBLIC_IP) {
            Write-Host "✓ Instance is running!" -ForegroundColor Green
            Write-Host "Public IP: $PUBLIC_IP" -ForegroundColor Green
            break
        }
        
        Write-Host "Current state: $STATE - waiting..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $retries++
    } catch {
        Write-Host "Checking instance status..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        $retries++
    }
}

if (-not $PUBLIC_IP) {
    Write-Host "Could not get public IP. Check AWS console." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== DEPLOYMENT SUMMARY ===" -ForegroundColor Green
Write-Host "Instance ID: $INSTANCE_ID" -ForegroundColor Cyan
Write-Host "Public IP: $PUBLIC_IP" -ForegroundColor Cyan
Write-Host "Security Group: $SG_ID" -ForegroundColor Cyan
Write-Host "Key File: ${KEY_NAME}.pem (in current directory)" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== NEXT STEPS ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. SSH into your instance:" -ForegroundColor White
Write-Host "   ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Once connected, follow these commands:" -ForegroundColor White
Write-Host "   sudo apt update && sudo apt upgrade -y" -ForegroundColor Cyan
Write-Host "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -" -ForegroundColor Cyan
Write-Host "   sudo apt install -y nodejs nginx python3.11 python3.11-venv python3-pip awscli git" -ForegroundColor Cyan
Write-Host "   git clone https://github.com/JaiAnshSB26/JBAC_AI_Trading_Coach.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Update your local environment.prod.ts with:" -ForegroundColor White
Write-Host "   apiUrl: 'http://${PUBLIC_IP}/api'" -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed setup instructions, see EC2_DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""

# Save deployment info
$DEPLOYMENT_INFO = @"
=== JBAC Trading Coach EC2 Deployment Info ===
Deployed: $(Get-Date)
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Security Group: $SG_ID
Region: $REGION
Key File: ${KEY_NAME}.pem

SSH Command:
ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}

Update environment.prod.ts:
apiUrl: 'http://${PUBLIC_IP}/api'
"@

$DEPLOYMENT_INFO | Out-File -FilePath "deployment_info.txt" -Encoding UTF8
Write-Host "Deployment info saved to deployment_info.txt" -ForegroundColor Green
Write-Host ""
Write-Host "Done! 🚀" -ForegroundColor Green
