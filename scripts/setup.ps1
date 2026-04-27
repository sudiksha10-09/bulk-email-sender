# Setup script for bulk email sender project (Windows PowerShell)

Write-Host "🚀 Setting up Bulk Email Sender..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚙️  Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env file with your configuration!" -ForegroundColor Red
}

# Generate SECRET_KEY if not set
$envContent = Get-Content .env -Raw
if ($envContent -match "your-secret-key-here-change-in-production") {
    Write-Host "🔑 Generating SECRET_KEY..." -ForegroundColor Yellow
    $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    $envContent = $envContent -replace "your-secret-key-here-change-in-production", $secretKey
    Set-Content .env $envContent
}

# Generate ENCRYPTION_KEY if not set
$envContent = Get-Content .env -Raw
if ($envContent -match "your-fernet-key-here") {
    Write-Host "🔐 Generating ENCRYPTION_KEY..." -ForegroundColor Yellow
    $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $envContent = $envContent -replace "your-fernet-key-here", $encryptionKey
    Set-Content .env $envContent
}

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your database, Redis, and API credentials"
Write-Host "2. Create PostgreSQL database: createdb bulk_email_sender"
Write-Host "3. Run migrations: python manage.py migrate"
Write-Host "4. Create superuser: python manage.py createsuperuser"
Write-Host "5. Start development server: python manage.py runserver"
Write-Host "6. Start Celery worker: celery -A config worker -l info"
