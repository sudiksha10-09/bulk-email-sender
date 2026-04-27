#!/bin/bash
# Script to run database migrations for Task 1.3
# This script applies all the initial migrations for the bulk email sender models

echo "🚀 Running Database Migrations for Task 1.3..."
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please configure it before running migrations."
    echo ""
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import django" 2>/dev/null; then
    echo "⚠️  Django not found. Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies are installed."
fi

echo ""
echo "🗄️  Running migrations..."
echo ""

# Run migrations
python manage.py migrate

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migrations completed successfully!"
    echo ""
    echo "📊 Database models created:"
    echo "  - User (authentication)"
    echo "  - SMTPConfig (smtp_config)"
    echo "  - RecipientList, Recipient (recipients)"
    echo "  - Template (templates)"
    echo "  - Campaign (campaigns)"
    echo "  - EmailLog, EmailEvent (tracking)"
    echo ""
    echo "🎯 Task 1.3 Complete!"
else
    echo ""
    echo "❌ Migration failed. Please check the error messages above."
    echo ""
    echo "Common issues:"
    echo "  1. PostgreSQL not running - Start PostgreSQL service"
    echo "  2. Database not created - Run: createdb bulk_email_sender"
    echo "  3. Wrong credentials in .env - Check DB_USER, DB_PASSWORD, DB_HOST"
    echo ""
fi
