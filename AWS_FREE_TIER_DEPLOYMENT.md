# AWS Free Tier Deployment Guide

## 🎉 Great News: Your Project CAN Run on AWS Free Tier!

AWS Free Tier includes:
- ✅ EC2 t2.micro instance (1 vCPU, 1GB RAM) - **12 months free**
- ✅ 30GB EBS storage - **12 months free**
- ✅ 5GB S3 storage - **12 months free**
- ✅ RDS db.t2.micro (PostgreSQL) - **12 months free**
- ✅ Route 53 hosted zone - **$0.50/month** (only cost)
- ✅ CloudFront CDN - 50GB transfer/month free
- ✅ Elastic IP (while instance is running) - **Free**

**Total Cost: $0.50-1.00/month for 12 months!**

---

## Prerequisites

1. **AWS Account** - Sign up at https://aws.amazon.com/free/
2. **Domain Name** (optional but recommended) - $10-15/year
3. **SSH Client** - Terminal (Mac/Linux) or PuTTY (Windows)
4. **Local Project** - Your smart_city project ready

---

## Architecture Overview

```
Internet
   ↓
Route 53 (DNS) → CloudFront (CDN) → S3 (Frontend Static Files)
                                  ↘
                                   EC2 (Backend API + Blender)
                                    ↓
                                   RDS (PostgreSQL Database)
```

---

## Step-by-Step Deployment

### Part 1: Launch EC2 Instance (Backend Server)

#### 1.1 Create EC2 Instance

1. **Login to AWS Console** → Navigate to **EC2**
2. **Click "Launch Instance"**
3. **Configure:**

```yaml
Name: smart-city-backend
AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
Instance Type: t2.micro (1GB RAM, 1 vCPU)
Key Pair: Create new → Download smart-city-key.pem
Network: Default VPC
Storage: 30GB gp3 (Free tier eligible)
Security Group: Create new
```

#### 1.2 Configure Security Group

**Inbound Rules:**

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | API (temporary) |

4. **Launch Instance**
5. **Allocate Elastic IP:**
   - EC2 → Elastic IPs → Allocate Elastic IP address
   - Associate with your instance

#### 1.3 Connect to EC2

```bash
# Set permissions for key file
chmod 400 smart-city-key.pem

# Connect via SSH
ssh -i smart-city-key.pem ubuntu@YOUR_ELASTIC_IP

# Or use EC2 Instance Connect from AWS Console
```

---

### Part 2: Setup Backend on EC2

#### 2.1 Install Dependencies

```bash
#!/bin/bash
# Run this on your EC2 instance

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL client (we'll use RDS for database)
sudo apt install -y postgresql-client

# Install Blender (headless)
sudo apt install -y blender

# Install Node.js 18 (for blockchain)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Git
sudo apt install -y git

# Install Nginx
sudo apt install -y nginx

# Install system dependencies
sudo apt install -y build-essential libpq-dev libgdal-dev gdal-bin
```

#### 2.2 Clone and Setup Project

```bash
# Create app directory
sudo mkdir -p /var/www
cd /var/www

# Clone your repository (or upload via SCP)
sudo git clone https://github.com/yourusername/smart_city.git
# OR upload using SCP from local machine:
# scp -i smart-city-key.pem -r /Users/ravindubandara/Desktop/smart_city ubuntu@YOUR_IP:/tmp/
# sudo mv /tmp/smart_city /var/www/

# Set permissions
sudo chown -R ubuntu:ubuntu /var/www/smart_city
cd smart_city/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-geo.txt
pip install gunicorn
```

#### 2.3 Setup Blockchain (if needed)

```bash
cd /var/www/smart_city/blockchain
npm install

# Generate wallet
node generate-wallet.js

# Save the output safely!
```

---

### Part 3: Setup RDS PostgreSQL Database

#### 3.1 Create RDS Instance

1. **AWS Console** → **RDS** → **Create database**

```yaml
Engine: PostgreSQL 14 or 15
Templates: Free tier
DB Instance Identifier: smart-city-db
Master Username: postgres
Master Password: [Generate strong password - SAVE IT!]
DB Instance Class: db.t3.micro (Free tier)
Storage: 20GB gp2
VPC: Same as EC2
Public Access: No
VPC Security Group: Create new → smart-city-db-sg
Initial Database Name: smart_city
```

#### 3.2 Configure Database Security Group

**In RDS Security Group (smart-city-db-sg):**

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| PostgreSQL | TCP | 5432 | EC2 Security Group ID | Allow EC2 to connect |

#### 3.3 Get Database Endpoint

1. **RDS** → **Databases** → **smart-city-db**
2. **Copy Endpoint:** `smart-city-db.xxxxx.us-east-1.rds.amazonaws.com`

#### 3.4 Test Connection from EC2

```bash
# On EC2 instance
psql -h smart-city-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d smart_city

# Enter password when prompted
# If successful, you'll see: smart_city=>
```

---

### Part 4: Configure Backend Environment

#### 4.1 Create Environment File

```bash
# On EC2
cd /var/www/smart_city/backend
nano .env
```

**Content:**

```env
# Database (Use your RDS endpoint)
DATABASE_URL=postgresql://postgres:YOUR_RDS_PASSWORD@smart-city-db.xxxxx.us-east-1.rds.amazonaws.com:5432/smart_city

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Update with your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,http://localhost:5173

# Blender
BLENDER_PATH=/usr/bin/blender

# Storage (Use S3 or local)
STORAGE_PATH=/var/www/smart_city/backend/storage

# AWS (for S3 storage - optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=smart-city-storage

# Blockchain
BLOCKCHAIN_ENABLED=true
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_blockchain_private_key

# API Settings
HOST=0.0.0.0
PORT=8000
WORKERS=2
```

#### 4.2 Run Database Migrations

```bash
cd /var/www/smart_city/backend
source venv/bin/activate
alembic upgrade head
```

---

### Part 5: Setup Backend Service

#### 5.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/smart-city-backend.service
```

**Content:**

```ini
[Unit]
Description=Smart City Backend API
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/smart_city/backend
Environment="PATH=/var/www/smart_city/backend/venv/bin"
EnvironmentFile=/var/www/smart_city/backend/.env
ExecStart=/var/www/smart_city/backend/venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /var/log/smart-city/access.log \
    --error-logfile /var/log/smart-city/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5.2 Create Log Directory

```bash
sudo mkdir -p /var/log/smart-city
sudo chown -R ubuntu:ubuntu /var/log/smart-city
```

#### 5.3 Start Backend Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable smart-city-backend

# Start service
sudo systemctl start smart-city-backend

# Check status
sudo systemctl status smart-city-backend

# View logs
sudo tail -f /var/log/smart-city/error.log
```

---

### Part 6: Configure Nginx Reverse Proxy

#### 6.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/smart-city
```

**Content:**

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - API Backend
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL certificates (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # File upload size
    client_max_body_size 100M;
}
```

#### 6.2 Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/smart-city /etc/nginx/sites-enabled/

# Remove default
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

### Part 7: Install SSL Certificate (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (option 2)

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Part 8: Setup S3 for Frontend (Static Hosting)

#### 8.1 Create S3 Bucket

1. **AWS Console** → **S3** → **Create bucket**

```yaml
Bucket name: smart-city-frontend (must be globally unique)
Region: us-east-1 (or closest to you)
Block Public Access: UNCHECK all (we need public access for website)
Bucket Versioning: Disabled
```

#### 8.2 Enable Static Website Hosting

1. **Bucket** → **Properties** → **Static website hosting**
2. **Enable**
3. **Index document:** `index.html`
4. **Error document:** `index.html`
5. **Save**

#### 8.3 Configure Bucket Policy

**Bucket** → **Permissions** → **Bucket Policy:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::smart-city-frontend/*"
        }
    ]
}
```

---

### Part 9: Build and Deploy Frontend

#### 9.1 Update Frontend Configuration

**On your local machine:**

```bash
cd /Users/ravindubandara/Desktop/smart_city/frontend

# Create production environment file
nano .env.production
```

**Content:**

```env
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_WS_URL=wss://api.yourdomain.com/ws
```

#### 9.2 Build Frontend

```bash
# Install dependencies
npm install

# Build for production
npm run build

# This creates a 'dist' folder
```

#### 9.3 Upload to S3

**Option 1: Using AWS CLI**

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
sudo apt install awscli  # Linux

# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output: json

# Upload to S3
aws s3 sync dist/ s3://smart-city-frontend/ --delete

# Set cache headers
aws s3 cp s3://smart-city-frontend/ s3://smart-city-frontend/ \
    --recursive \
    --metadata-directive REPLACE \
    --cache-control max-age=31536000,public \
    --exclude "index.html" \
    --exclude "*.html"

# HTML files should not be cached
aws s3 cp s3://smart-city-frontend/ s3://smart-city-frontend/ \
    --recursive \
    --metadata-directive REPLACE \
    --cache-control no-cache,no-store,must-revalidate \
    --content-type "text/html" \
    --include "*.html"
```

**Option 2: Using S3 Console**

1. **S3** → **smart-city-frontend** → **Upload**
2. **Add files** → Select all files from `dist` folder
3. **Upload**

---

### Part 10: Setup CloudFront CDN (Optional but Recommended)

#### 10.1 Create CloudFront Distribution

1. **AWS Console** → **CloudFront** → **Create distribution**

```yaml
Origin Domain: smart-city-frontend.s3.us-east-1.amazonaws.com
Origin Path: Leave empty
Name: smart-city-frontend-s3
Enable Origin Shield: No

Default Cache Behavior:
  Viewer Protocol Policy: Redirect HTTP to HTTPS
  Allowed HTTP Methods: GET, HEAD, OPTIONS
  Cache Policy: CachingOptimized

Settings:
  Price Class: Use Only North America and Europe (cheapest)
  Alternate Domain Names (CNAMEs): yourdomain.com, www.yourdomain.com
  Custom SSL Certificate: Request certificate (see below)
  Default Root Object: index.html
```

#### 10.2 Request SSL Certificate (CloudFront)

1. **AWS Certificate Manager (ACM)** → **Request certificate**
2. **Public certificate**
3. **Domain names:**
   - `yourdomain.com`
   - `*.yourdomain.com`
4. **Validation method:** DNS validation
5. **Add CNAME records to your domain's DNS** (copy from ACM)
6. **Wait for validation** (5-30 minutes)

#### 10.3 Configure Custom Error Pages

**CloudFront Distribution** → **Error Pages:**

| HTTP Error Code | Response Page Path | HTTP Response Code |
|----------------|-------------------|-------------------|
| 403 | /index.html | 200 |
| 404 | /index.html | 200 |

This ensures React Router works correctly.

---

### Part 11: Configure DNS (Route 53 or Your Registrar)

#### Option A: Using Route 53

1. **Route 53** → **Hosted zones** → **Create hosted zone**
2. **Domain name:** `yourdomain.com`
3. **Create**

**Create Records:**

```yaml
# Frontend (CloudFront)
Record 1:
  Name: yourdomain.com
  Type: A
  Alias: Yes
  Alias Target: CloudFront distribution

Record 2:
  Name: www.yourdomain.com
  Type: A
  Alias: Yes
  Alias Target: CloudFront distribution

# Backend API
Record 3:
  Name: api.yourdomain.com
  Type: A
  Value: Your EC2 Elastic IP
```

4. **Update nameservers at your domain registrar** with Route 53 nameservers

#### Option B: Using External DNS (Namecheap, GoDaddy, etc.)

**Add these records:**

```
A Record: @ → CloudFront distribution IP (or CNAME to CloudFront)
A Record: www → CloudFront distribution IP
A Record: api → EC2 Elastic IP
```

---

## Part 12: Testing

### 12.1 Test Backend API

```bash
# From your local machine
curl https://api.yourdomain.com/api/v1/health

# Should return: {"status":"healthy"}
```

### 12.2 Test Frontend

1. **Open browser:** `https://yourdomain.com`
2. **Check console** for errors (F12)
3. **Try login/register**
4. **Test file upload**
5. **Test 3D generation**

### 12.3 Monitor Logs

```bash
# SSH to EC2
ssh -i smart-city-key.pem ubuntu@YOUR_IP

# Backend logs
sudo tail -f /var/log/smart-city/error.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u smart-city-backend -f
```

---

## Cost Monitoring & Optimization

### Free Tier Limits (First 12 Months)

✅ **EC2:** 750 hours/month (1 t2.micro = 100% usage, OK)
✅ **RDS:** 750 hours/month (1 db.t3.micro = 100% usage, OK)
✅ **S3:** 5GB storage, 20,000 GET, 2,000 PUT requests/month
✅ **CloudFront:** 50GB data transfer out/month
✅ **Route 53:** $0.50/month for hosted zone

### Set Up Billing Alerts

1. **AWS Console** → **Billing** → **Budgets**
2. **Create budget**
3. **Type:** Cost budget
4. **Amount:** $5/month
5. **Email alerts** when 80% and 100% of budget

### After Free Tier (Months 13+)

Estimated monthly costs:
- EC2 t2.micro: $8-10/month
- RDS db.t3.micro: $12-15/month
- S3 + CloudFront: $1-3/month
- **Total: ~$20-30/month**

**Optimization options:**
- Switch to Reserved Instances (save 40%)
- Use EC2 Spot Instances (save 70%, but can be interrupted)
- Downgrade RDS or use EC2-hosted PostgreSQL
- Use Lightsail instead ($3.50-5/month for VPS)

---

## Backup & Disaster Recovery

### 12.1 Database Backups (RDS)

**Automated (Free Tier includes 20GB):**

1. **RDS** → **smart-city-db** → **Modify**
2. **Backup retention period:** 7 days
3. **Preferred backup window:** 03:00-04:00 UTC
4. **Apply immediately**

**Manual Snapshots:**

```bash
# Create snapshot
aws rds create-db-snapshot \
    --db-instance-identifier smart-city-db \
    --db-snapshot-identifier smart-city-backup-$(date +%Y%m%d)
```

### 12.2 EC2 Backups (AMI)

1. **EC2** → **Instances** → Select instance
2. **Actions** → **Image and templates** → **Create image**
3. **Name:** smart-city-backend-backup-YYYYMMDD
4. **Create**

**Automated with cron:**

```bash
# On EC2
crontab -e

# Add (weekly backup at 2 AM Sunday):
0 2 * * 0 /home/ubuntu/scripts/backup.sh
```

**backup.sh:**

```bash
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
DATE=$(date +%Y%m%d)

aws ec2 create-image \
    --instance-id $INSTANCE_ID \
    --name "smart-city-backup-$DATE" \
    --description "Automated backup" \
    --region us-east-1
```

### 12.3 S3 Versioning

1. **S3** → **smart-city-frontend** → **Properties**
2. **Bucket Versioning** → **Enable**

---

## Maintenance & Updates

### Update Frontend

```bash
# On local machine
cd frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://smart-city-frontend/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/*"
```

### Update Backend

```bash
# SSH to EC2
ssh -i smart-city-key.pem ubuntu@YOUR_IP

# Pull latest code
cd /var/www/smart_city
git pull origin main

# Update dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart service
sudo systemctl restart smart-city-backend

# Check status
sudo systemctl status smart-city-backend
```

---

## Troubleshooting

### EC2 Instance Not Responding

```bash
# Check if running
aws ec2 describe-instances --instance-ids i-xxxxx

# Reboot
aws ec2 reboot-instances --instance-ids i-xxxxx

# Connect via console if SSH fails
# EC2 Console → Instance → Connect → EC2 Instance Connect
```

### Backend Service Issues

```bash
# Check service status
sudo systemctl status smart-city-backend

# View recent logs
sudo journalctl -u smart-city-backend -n 100

# Restart service
sudo systemctl restart smart-city-backend

# Check if port is listening
sudo netstat -tlnp | grep 8000
```

### Database Connection Issues

```bash
# Test from EC2
psql -h smart-city-db.xxxxx.rds.amazonaws.com -U postgres -d smart_city

# Check security group allows EC2
# RDS Console → smart-city-db → Connectivity & Security → VPC security groups

# Check if RDS is running
aws rds describe-db-instances --db-instance-identifier smart-city-db
```

### CloudFront Not Serving Latest Files

```bash
# Invalidate cache
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/*"

# Check distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID
```

---

## Security Hardening

### 12.1 EC2 Security

```bash
# Update packages regularly
sudo apt update && sudo apt upgrade -y

# Install fail2ban (protects against brute force)
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 12.2 Restrict Security Groups

**EC2 Security Group:**
- Only allow SSH from your IP (not 0.0.0.0/0)
- Remove port 8000 access (only Nginx should be public)

**RDS Security Group:**
- Only allow PostgreSQL from EC2 security group
- No public access

### 12.3 Environment Variables

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use AWS Secrets Manager (optional, costs $0.40/secret/month)
aws secretsmanager create-secret \
    --name smart-city/database \
    --secret-string '{"host":"...","password":"..."}'
```

---

## Complete Deployment Checklist

### Pre-Deployment
- [ ] AWS account created and verified
- [ ] Domain name purchased (optional)
- [ ] Project built locally and tested
- [ ] Environment variables prepared

### Backend Setup
- [ ] EC2 instance launched (t2.micro)
- [ ] Elastic IP allocated and associated
- [ ] Security groups configured
- [ ] SSH access working
- [ ] Dependencies installed
- [ ] Project code uploaded
- [ ] Python virtual environment created

### Database Setup
- [ ] RDS instance created (db.t3.micro)
- [ ] Security group configured
- [ ] Database connection tested from EC2
- [ ] Migrations run successfully

### Backend Service
- [ ] Environment file configured
- [ ] Systemd service created
- [ ] Service started and enabled
- [ ] Nginx installed and configured
- [ ] SSL certificate installed
- [ ] API accessible via HTTPS

### Frontend Setup
- [ ] S3 bucket created
- [ ] Static website hosting enabled
- [ ] Bucket policy configured
- [ ] Frontend built with production config
- [ ] Files uploaded to S3
- [ ] CloudFront distribution created
- [ ] SSL certificate for CloudFront
- [ ] Custom error pages configured

### DNS Configuration
- [ ] Route 53 hosted zone created (or DNS records added)
- [ ] A records for frontend pointing to CloudFront
- [ ] A record for API pointing to EC2 Elastic IP
- [ ] DNS propagation complete

### Testing
- [ ] Frontend loads at https://yourdomain.com
- [ ] API responds at https://api.yourdomain.com/api/v1/health
- [ ] Login/authentication works
- [ ] File uploads work
- [ ] 3D model generation works
- [ ] No console errors

### Monitoring & Maintenance
- [ ] Billing alerts configured
- [ ] CloudWatch alarms set up
- [ ] Database backups enabled
- [ ] EC2 AMI backup created
- [ ] Update procedure documented

---

## Quick Reference Commands

### SSH to EC2
```bash
ssh -i smart-city-key.pem ubuntu@YOUR_ELASTIC_IP
```

### Restart Backend
```bash
sudo systemctl restart smart-city-backend
```

### View Logs
```bash
sudo tail -f /var/log/smart-city/error.log
```

### Update Frontend
```bash
aws s3 sync dist/ s3://smart-city-frontend/ --delete
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

### Database Backup
```bash
pg_dump -h RDS_ENDPOINT -U postgres -d smart_city > backup.sql
```

### Check Service Status
```bash
sudo systemctl status smart-city-backend
```

---

## Additional Resources

- **AWS Free Tier Details:** https://aws.amazon.com/free/
- **AWS CLI Documentation:** https://docs.aws.amazon.com/cli/
- **EC2 User Guide:** https://docs.aws.amazon.com/ec2/
- **RDS User Guide:** https://docs.aws.amazon.com/rds/
- **S3 Static Website:** https://docs.aws.amazon.com/s3/
- **CloudFront Guide:** https://docs.aws.amazon.com/cloudfront/

---

## Summary

**✅ Your Smart City project can run completely free on AWS for 12 months!**

**What you get:**
- Professional infrastructure
- Auto-scaling capabilities
- Free SSL certificates
- CDN for fast global access
- Managed database with automatic backups
- 99.9% uptime SLA

**After 12 months:** ~$20-30/month or migrate to AWS Lightsail for $5-10/month

**Need help?** Check the troubleshooting section or AWS Support (free for billing/account issues).

Good luck with your deployment! 🚀
