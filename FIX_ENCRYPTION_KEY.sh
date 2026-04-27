#!/bin/bash

# Fix ENCRYPTION_KEY error - Rebuild Docker

echo "🔧 Fixing ENCRYPTION_KEY error..."
echo ""

# Stop containers
echo "1️⃣  Stopping containers..."
docker compose down

# Rebuild image
echo "2️⃣  Rebuilding Docker image..."
docker compose build --no-cache

# Start containers
echo "3️⃣  Starting containers..."
docker compose up -d

# Check logs
echo "4️⃣  Checking logs..."
sleep 5
docker compose logs webmyapp_web | tail -20

echo ""
echo "✅ Done! Access app at: http://YOUR_VPS_IP/app/"
