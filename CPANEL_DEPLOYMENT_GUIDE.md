# cPanel Shared Hosting Deployment Guide

## ⚠️ Important Limitations

**Shared hosting has significant limitations for this project:**

1. **Python/FastAPI Backend**: Most shared hosting doesn't support Python applications or FastAPI
2. **Blender**: Cannot run Blender (requires significant resources and system access)
3. **Node.js**: Limited or no Node.js support on most shared hosting
4. **PostgreSQL**: May not be available (usually only MySQL/MariaDB)
5. **Long-running processes**: Backend services cannot run continuously
6. **Resource limits**: CPU, memory, and execution time are severely restricted

## Recommended Alternative: VPS Hosting

For this project, **VPS hosting is strongly recommended** instead of shared hosting:
- DigitalOcean ($6/month)
- Linode ($5/month)
- Vultr ($6/month)
- AWS Lightsail ($5/month)

---

## If You Must Use Shared Hosting: Static Frontend Only

You can deploy **only the frontend** as a static site on shared hosting. The backend must be hosted elsewhere.

### Prerequisites

- cPanel account with:
  - File Manager or FTP access
  - Custom domain or subdomain
  - SSL certificate support

### Step 1: Build the Frontend

On your local machine:

```bash
cd /Users/ravindubandara/Desktop/smart_city/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

This creates a `dist` folder with optimized static files.

### Step 2: Configure Backend URL

Before building, update the backend API URL to point to your VPS/cloud backend:

**File: `frontend/src/config.ts`** (create if doesn't exist):

```typescript
export const API_BASE_URL = process.env.VITE_API_URL || 'https://your-backend-domain.com/api/v1';
export const WS_BASE_URL = process.env.VITE_WS_URL || 'wss://your-backend-domain.com/ws';
```

**File: `frontend/.env.production`**:

```env
VITE_API_URL=https://your-backend-domain.com/api/v1
VITE_WS_URL=wss://your-backend-domain.com/ws
```

Rebuild after updating:

```bash
npm run build
```

### Step 3: Upload to cPanel

#### Option A: Using File Manager

1. **Login to cPanel**
2. **Navigate to File Manager**
3. **Go to public_html** (or your domain's document root)
4. **Delete default files** (index.html, etc.)
5. **Upload the contents of `dist` folder**:
   - Click "Upload" button
   - Select all files from `frontend/dist/`
   - Wait for upload to complete
6. **Set permissions**:
   - Files: 644
   - Folders: 755

#### Option B: Using FTP

1. **Get FTP credentials from cPanel**
2. **Use an FTP client** (FileZilla, Cyberduck):
   - Host: ftp.yourdomain.com
   - Username: your-cpanel-username
   - Password: your-cpanel-password
   - Port: 21
3. **Navigate to public_html**
4. **Upload all files from `frontend/dist/`**

### Step 4: Configure URL Rewriting

For React Router to work, create/update `.htaccess`:

**File: `public_html/.htaccess`**:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  
  # Don't rewrite files or directories
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  
  # Rewrite everything else to index.html
  RewriteRule ^ index.html [L]
</IfModule>

# Enable Gzip compression
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Browser caching
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpg "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType application/json "access plus 1 week"
  ExpiresByType application/pdf "access plus 1 month"
  ExpiresByType application/x-font-woff "access plus 1 year"
  ExpiresByType application/font-woff2 "access plus 1 year"
</IfModule>

# Security headers
<IfModule mod_headers.c>
  Header set X-Content-Type-Options "nosniff"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set X-XSS-Protection "1; mode=block"
</IfModule>
```

### Step 5: SSL Certificate

1. **In cPanel, go to SSL/TLS Status**
2. **Enable AutoSSL** (free Let's Encrypt certificate)
3. **Or install custom certificate** if you have one
4. **Force HTTPS** by adding to `.htaccess`:

```apache
# Force HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

---

## Backend Deployment (Required - Use VPS)

Since the backend cannot run on shared hosting, deploy it to a VPS:

### Option 1: DigitalOcean Droplet

**Quick Setup Script:**

```bash
#!/bin/bash
# Run this on your VPS after SSH login

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Nginx
sudo apt install -y nginx

# Install Blender (headless)
sudo apt install -y blender

# Install Node.js (for blockchain)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Clone your repository
cd /var/www
sudo git clone https://github.com/yourusername/smart_city.git
sudo chown -R $USER:$USER smart_city
cd smart_city

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE smart_city;"
sudo -u postgres psql -c "CREATE USER smart_city_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smart_city TO smart_city_user;"

# Run migrations
alembic upgrade head

# Setup systemd service
sudo nano /etc/systemd/system/smart-city-backend.service
```

**Systemd Service File:**

```ini
[Unit]
Description=Smart City Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/smart_city/backend
Environment="PATH=/var/www/smart_city/backend/venv/bin"
ExecStart=/var/www/smart_city/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Start Services:**

```bash
# Enable and start backend
sudo systemctl daemon-reload
sudo systemctl enable smart-city-backend
sudo systemctl start smart-city-backend

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Install SSL certificate
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### Option 2: Docker Deployment (Easiest)

**On your VPS:**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Clone repository
git clone https://github.com/yourusername/smart_city.git
cd smart_city

# Create environment file
cp .env.example .env
nano .env  # Edit with your production values

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://smart_city_user:your_password@localhost/smart_city

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (add your cPanel domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Blender
BLENDER_PATH=/usr/bin/blender

# Storage
STORAGE_PATH=/var/www/smart_city/backend/storage

# Blockchain
BLOCKCHAIN_ENABLED=true
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_ethereum_private_key
```

### Frontend (.env.production)

```env
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_WS_URL=wss://api.yourdomain.com/ws
```

---

## DNS Configuration

### For cPanel Frontend

1. **Point your domain to cPanel server**:
   - A Record: `@` → Your cPanel server IP
   - CNAME: `www` → `yourdomain.com`

### For VPS Backend

2. **Point subdomain to VPS**:
   - A Record: `api` → Your VPS IP address
   - Wait for DNS propagation (up to 48 hours)

---

## Deployment Checklist

### Pre-Deployment

- [ ] Backend deployed to VPS and running
- [ ] Database created and migrations run
- [ ] API endpoint accessible (https://api.yourdomain.com)
- [ ] Frontend `.env.production` updated with backend URL
- [ ] Frontend built with `npm run build`
- [ ] SSL certificates installed on both frontend and backend

### Frontend Upload

- [ ] All `dist` files uploaded to `public_html`
- [ ] `.htaccess` file configured for URL rewriting
- [ ] File permissions set correctly (644 for files, 755 for folders)
- [ ] Domain points to cPanel server
- [ ] SSL certificate active and HTTPS forced

### Backend Setup

- [ ] PostgreSQL database running
- [ ] Backend service running (systemd or Docker)
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate for API subdomain installed
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] CORS configured to allow frontend domain

### Testing

- [ ] Frontend loads at https://yourdomain.com
- [ ] No console errors in browser
- [ ] Login/authentication works
- [ ] API calls succeed
- [ ] File uploads work
- [ ] 3D model generation works
- [ ] Database operations succeed

---

## Maintenance & Updates

### Updating Frontend

```bash
# On local machine
cd frontend
npm run build

# Upload new dist files to cPanel
# (Overwrites old files)
```

### Updating Backend

```bash
# On VPS
cd /var/www/smart_city
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart smart-city-backend
```

---

## Troubleshooting

### Frontend Issues

**Blank page or 404 errors:**
- Check `.htaccess` is present and correct
- Verify all files uploaded
- Check browser console for errors
- Ensure HTTPS is working

**API calls failing:**
- Check CORS settings in backend
- Verify API URL in frontend config
- Check SSL certificate on API domain
- Test API endpoint directly: `https://api.yourdomain.com/api/v1/health`

### Backend Issues

**Service won't start:**
```bash
sudo systemctl status smart-city-backend
sudo journalctl -u smart-city-backend -f
```

**Database connection errors:**
```bash
sudo -u postgres psql
\l  # List databases
\c smart_city  # Connect to database
\dt  # List tables
```

**Nginx errors:**
```bash
sudo nginx -t  # Test configuration
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

---

## Performance Optimization

### Frontend

1. **Enable compression in `.htaccess`** (already included above)
2. **Use CDN** for static assets (Cloudflare free tier)
3. **Optimize images** before uploading
4. **Enable caching** (already included in `.htaccess`)

### Backend

1. **Use Redis for caching**:
```bash
sudo apt install -y redis-server
pip install redis
```

2. **Increase Uvicorn workers**:
```bash
# In systemd service
ExecStart=... --workers 4
```

3. **Database optimization**:
```sql
-- Add indexes
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
```

---

## Cost Breakdown

### Minimum Setup

| Service | Provider | Cost |
|---------|----------|------|
| Frontend Hosting | cPanel Shared Hosting | $3-10/month |
| Backend VPS | DigitalOcean/Vultr | $6-12/month |
| Domain Name | Namecheap/GoDaddy | $10-15/year |
| **Total** | | **~$10-25/month** |

### Recommended Setup

| Service | Provider | Cost |
|---------|----------|------|
| VPS (2GB RAM) | DigitalOcean | $12/month |
| Domain Name | Namecheap | $12/year |
| Backups | DigitalOcean | $2/month |
| **Total** | | **~$15/month** |

---

## Alternative: Full VPS Deployment

**For best results, host both frontend and backend on the same VPS:**

1. Build frontend locally
2. Upload `dist` to VPS `/var/www/html`
3. Configure Nginx to serve both:

```nginx
# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        # ... proxy headers ...
    }
}
```

This eliminates the need for cPanel entirely and gives you full control.

---

## Summary

**Recommended approach:**
1. ❌ Don't use shared hosting for this full-stack application
2. ✅ Use VPS hosting ($6-12/month) for complete project
3. ✅ Or: Frontend on cPanel + Backend on VPS (split approach)

**The project requires:**
- Python backend with FastAPI
- PostgreSQL database
- Blender for 3D generation
- Node.js for blockchain
- Long-running background processes

**None of these are typically available on shared hosting.**

Would you like me to create specific setup scripts for your preferred VPS provider (DigitalOcean, Linode, AWS, etc.)?
