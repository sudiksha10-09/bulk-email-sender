#!/bin/bash

# Setup script for bulk email sender project

echo "🚀 Setting up Bulk Email Sender..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
fi

# Generate SECRET_KEY if not set
if grep -q "your-secret-key-here-change-in-production" .env; then
    echo "🔑 Generating SECRET_KEY..."
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
fi

# Generate ENCRYPTION_KEY if not set
if grep -q "your-fernet-key-here" .env; then
    echo "🔐 Generating ENCRYPTION_KEY..."
    ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s/your-fernet-key-here/$ENCRYPTION_KEY/" .env
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database, Redis, and API credentials"
echo "2. Create PostgreSQL database: createdb bulk_email_sender"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Start development server: python manage.py runserver"
echo "6. Start Celery worker: celery -A config worker -l info"
