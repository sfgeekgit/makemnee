# Production Deployment Guide

This guide covers deploying the MakeMNEE API to production with Caddy as a reverse proxy and automatic SSL.

## Prerequisites

- Domain name pointing to your server (e.g., makemnee.com)
- Ubuntu server with sudo access
- Python 3.10+ installed

## Step 1: Install Caddy

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

## Step 2: Set Up the API as a System Service

```bash
# Copy the service file
sudo cp /home/mnee/backend/makemnee-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable makemnee-api

# Start the service
sudo systemctl start makemnee-api

# Check status
sudo systemctl status makemnee-api
```

## Step 3: Configure Caddy

```bash
# Edit the Caddyfile to use your domain
sudo nano /home/mnee/backend/Caddyfile

# Replace "makemnee.com" with your actual domain

# Copy Caddyfile to Caddy's config directory
sudo cp /home/mnee/backend/Caddyfile /etc/caddy/Caddyfile

# Test Caddy configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy (will automatically get SSL certificate)
sudo systemctl reload caddy
```

## Step 4: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Optional: Allow SSH if not already allowed
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

## Step 5: Test the Deployment

```bash
# Check if API is running
curl http://localhost:8000/health

# Check if Caddy is serving with SSL
curl https://makemnee.com/health
```

## Deployment Checklist

- [ ] Domain DNS points to server IP
- [ ] Caddy installed and configured
- [ ] API service running (systemctl status makemnee-api)
- [ ] SSL certificate obtained automatically (Caddy handles this)
- [ ] Firewall configured (ports 80, 443 open)
- [ ] Database file permissions correct
- [ ] Environment variables set if needed

## Monitoring

### Check API logs
```bash
# View API service logs
sudo journalctl -u makemnee-api -f

# View recent errors
sudo journalctl -u makemnee-api -n 50 --no-pager
```

### Check Caddy logs
```bash
# View Caddy logs
sudo journalctl -u caddy -f

# View access logs
sudo tail -f /var/log/caddy/makemnee.log
```

### Check service status
```bash
# API status
sudo systemctl status makemnee-api

# Caddy status
sudo systemctl status caddy
```

## Updating the API

```bash
# Pull latest code (if using git)
cd /home/mnee
git pull

# Activate virtual environment
cd backend
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart makemnee-api

# Check it's running
sudo systemctl status makemnee-api
```

## SSL Certificate Renewal

Caddy automatically renews SSL certificates before they expire. No manual intervention needed!

To check certificate status:
```bash
sudo caddy list-certificates
```

## Production Environment Variables

Create `/home/mnee/backend/.env` for production settings:

```bash
# Database (SQLite by default)
DATABASE_URL=sqlite:///./bountyboard.db

# Or use PostgreSQL for production scale:
# DATABASE_URL=postgresql://user:pass@localhost/makemnee

# Server
ENVIRONMENT=production
HOST=127.0.0.1
PORT=8000
```

## Scaling Considerations

### Current Setup (Good for MVP)
- Single uvicorn process with 4 workers
- SQLite database
- Handles ~100-1000 requests/minute

### For Higher Scale
1. **Use PostgreSQL** instead of SQLite
2. **Use Gunicorn** with multiple uvicorn workers
3. **Add Redis** for caching
4. **Load balancer** for multiple API servers

Example with Gunicorn:
```bash
# Install gunicorn
pip install gunicorn

# Update systemd service ExecStart to:
ExecStart=/home/mnee/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
cat > /home/mnee/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/mnee/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/mnee/backend/bountyboard.db $BACKUP_DIR/bountyboard_$DATE.db
# Keep only last 30 days
find $BACKUP_DIR -name "bountyboard_*.db" -mtime +30 -delete
EOF

chmod +x /home/mnee/backup-db.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/mnee/backup-db.sh") | crontab -
```

## Security Best Practices

1. **Keep system updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Restrict API to localhost** (Caddy handles external traffic)
   - API binds to 127.0.0.1:8000 (not 0.0.0.0)
   - Only Caddy can access it

3. **Database permissions**
   ```bash
   chmod 600 /home/mnee/backend/bountyboard.db
   ```

4. **Monitor logs for suspicious activity**

5. **Rate limiting** (can add to Caddy or API level)

## Troubleshooting

### API not starting
```bash
# Check logs
sudo journalctl -u makemnee-api -n 100

# Check if port is in use
sudo lsof -i :8000

# Test manually
cd /home/mnee/backend
source venv/bin/activate
python run.py
```

### Caddy not getting SSL certificate
```bash
# Check Caddy logs
sudo journalctl -u caddy -n 100

# Verify domain resolves to server
dig makemnee.com

# Check ports are open
sudo ufw status
```

### Database locked error
```bash
# Stop API
sudo systemctl stop makemnee-api

# Check for stale connections
sudo lsof /home/mnee/backend/bountyboard.db

# Start API
sudo systemctl start makemnee-api
```

## Alternative: Nginx + Certbot

If you prefer Nginx over Caddy:

### Install Nginx and Certbot
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name makemnee.com www.makemnee.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Get SSL Certificate
```bash
sudo certbot --nginx -d makemnee.com -d www.makemnee.com
```

## Summary

**Recommended production stack:**
- **Caddy** (reverse proxy + automatic SSL)
- **Uvicorn** (ASGI server for FastAPI)
- **SQLite** (database for MVP; PostgreSQL for scale)
- **Systemd** (process management)

**Yes, you can set up SSL now!** Caddy makes it trivial - just point your domain to the server and run the commands above. SSL will be configured automatically.
