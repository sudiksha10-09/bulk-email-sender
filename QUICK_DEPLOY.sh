#!/bin/bash
# Quick deployment script for auth fix

set -e

echo "🔧 BulkMail Auth Fix - Deployment Script"
echo "=========================================="

# Navigate to project directory
cd /opt/myapp-docker

echo "📦 Stopping containers..."
docker compose down

echo "🔨 Rebuilding Docker image..."
docker compose build --no-cache

echo "🚀 Starting containers..."
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 5

echo "📋 Checking logs..."
docker compose logs webmyapp_web | tail -20

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 Testing:"
echo "1. Open http://your-vps-ip/app/"
echo "2. Click 'Create Account'"
echo "3. Enter test credentials"
echo "4. Should see success message"
echo "5. Click 'Sign In' and log in with same credentials"
echo ""
echo "📊 Monitor logs:"
echo "   docker compose logs -f webmyapp_web"
echo ""
echo "🔍 Check for POST requests:"
echo "   docker compose logs webmyapp_web | grep 'POST.*auth'"
