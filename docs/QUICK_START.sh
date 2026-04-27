#!/bin/bash

# Quick Start Script for Docker Deployment
# Run this on your Ubuntu 20.04 VPS

set -e

echo "=========================================="
echo "MyApp Docker Deployment - Quick Start"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: Create directories
echo -e "${YELLOW}Step 1: Creating directories...${NC}"
mkdir -p /opt/myapp-docker
mkdir -p /opt/myapp-docker/app
mkdir -p /opt/myapp-docker/logs
mkdir -p /opt/myapp-docker/static
mkdir -p /opt/myapp-docker/media
mkdir -p /opt/myapp-docker/postgres_data
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 2: Check Docker installation
echo -e "${YELLOW}Step 2: Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Installing Docker...${NC}"
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose not found. Installing...${NC}"
    apt-get install -y docker-compose
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
fi
echo ""

# Step 3: Verify existing containers
echo -e "${YELLOW}Step 3: Verifying existing containers...${NC}"
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
echo ""
echo -e "${GREEN}✓ Existing containers verified${NC}"
echo ""

# Step 4: Create .env file
echo -e "${YELLOW}Step 4: Creating .env file...${NC}"
if [ ! -f /opt/myapp-docker/.env ]; then
    cat > /opt/myapp-docker/.env << 'EOF'
DEBUG=False
SECRET_KEY=django-insecure-change-this-to-a-long-random-string-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP
DB_NAME=myapp_db
DB_USER=myapp_user
DB_PASSWORD=ChangeThisSecurePassword123!
REDIS_URL=redis://redis:6379/0
EOF
    echo -e "${YELLOW}⚠ .env file created. Please edit it with your values:${NC}"
    echo "   nano /opt/myapp-docker/.env"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Step 5: Set permissions
echo -e "${YELLOW}Step 5: Setting permissions...${NC}"
chown -R $SUDO_USER:$SUDO_USER /opt/myapp-docker
chmod 600 /opt/myapp-docker/.env
chmod -R 755 /opt/myapp-docker
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Step 6: Create systemd service
echo -e "${YELLOW}Step 6: Creating systemd service...${NC}"
cat > /etc/systemd/system/myapp-docker.service << 'EOF'
[Unit]
Description=MyApp Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/myapp-docker
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
RemainAfterExit=yes
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable myapp-docker.service
echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

# Step 7: Summary
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit environment variables:"
echo "   nano /opt/myapp-docker/.env"
echo ""
echo "2. Upload your Django application:"
echo "   scp -r /path/to/project/* root@YOUR_SERVER_IP:/opt/myapp-docker/app/"
echo ""
echo "3. Copy Dockerfile and docker-compose.yml to /opt/myapp-docker/"
echo ""
echo "4. Build and start containers:"
echo "   cd /opt/myapp-docker"
echo "   docker-compose build"
echo "   docker-compose up -d"
echo ""
echo "5. Create superuser:"
echo "   docker-compose exec web python manage.py createsuperuser"
echo ""
echo "6. Access your app:"
echo "   http://YOUR_SERVER_IP:9000"
echo ""
echo "7. Configure existing nginx to proxy:"
echo "   See DOCKER_DEPLOYMENT_GUIDE.md Step 10"
echo ""
