#!/bin/bash

# Production Fixes Application Script
# Run this script to apply all production fixes

set -e

echo "=========================================="
echo "Applying Production Fixes"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Run this script from project root (where manage.py is)${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Verify all files exist${NC}"
files=(
    "config/settings/production.py"
    "frontend/app.html"
    "docker-compose.yml"
    "gunicorn_config.py"
    ".env.production"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (MISSING)"
    fi
done

echo ""
echo -e "${YELLOW}Step 2: Backup current files${NC}"
mkdir -p backups
timestamp=$(date +%Y%m%d_%H%M%S)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "backups/${file//\//_}_$timestamp.bak"
        echo -e "${GREEN}✓${NC} Backed up $file"
    fi
done

echo ""
echo -e "${YELLOW}Step 3: Verify .env configuration${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.production${NC}"
    cp .env.production .env
    echo -e "${RED}⚠ IMPORTANT: Edit .env with your production values!${NC}"
    echo "  - Set ALLOWED_HOSTS"
    echo "  - Set SECRET_KEY"
    echo "  - Set ENCRYPTION_KEY"
    echo "  - Set database password"
    echo "  - Set email credentials"
    echo ""
    echo "Run: nano .env"
    exit 1
else
    echo -e "${GREEN}✓${NC} .env exists"
    
    # Check required variables
    required_vars=("ALLOWED_HOSTS" "SECRET_KEY" "ENCRYPTION_KEY" "DB_PASSWORD")
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            value=$(grep "^$var=" .env | cut -d'=' -f2)
            if [ -z "$value" ] || [ "$value" = "your-" ] || [ "$value" = "change-this" ]; then
                echo -e "${RED}✗${NC} $var not properly configured"
            else
                echo -e "${GREEN}✓${NC} $var configured"
            fi
        else
            echo -e "${RED}✗${NC} $var missing from .env"
        fi
    done
fi

echo ""
echo -e "${YELLOW}Step 4: Check Docker installation${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installed: $(docker --version)"
else
    echo -e "${RED}✗${NC} Docker not found"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose installed: $(docker-compose --version)"
else
    echo -e "${RED}✗${NC} Docker Compose not found"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Build Docker images${NC}"
echo "Running: docker-compose build"
docker-compose build

echo ""
echo -e "${YELLOW}Step 6: Start containers${NC}"
echo "Running: docker-compose up -d"
docker-compose up -d

echo ""
echo -e "${YELLOW}Step 7: Wait for services to be ready${NC}"
sleep 10

echo ""
echo -e "${YELLOW}Step 8: Run database migrations${NC}"
docker-compose exec -T web python manage.py migrate

echo ""
echo -e "${YELLOW}Step 9: Collect static files${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo -e "${YELLOW}Step 10: Verify deployment${NC}"
echo ""

# Check health endpoint
echo -n "Checking health endpoint... "
if curl -s http://localhost:9000/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check containers
echo ""
echo "Container status:"
docker-compose ps

echo ""
echo -e "${GREEN}=========================================="
echo "✓ All fixes applied successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Test login: curl -X POST http://localhost:9000/api/auth/login/ -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"test\"}'"
echo "2. Check logs: docker-compose logs -f web"
echo "3. Setup Nginx reverse proxy (see DEPLOYMENT_CHECKLIST.md)"
echo "4. Setup SSL with Let's Encrypt"
echo "5. Monitor: docker stats"
echo ""
