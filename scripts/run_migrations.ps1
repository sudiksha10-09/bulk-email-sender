# Script to run database migrations for Task 1.3
# This script applies all the initial migrations for the bulk email sender models

Write-Host "🚀 Running Database Migrations for Task 1.3..." -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Created .env file. Please configure it before running migrations." -ForegroundColor Green
    Write-Host ""
}

# Check if dependencies are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
try {
    py -c "import django" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Django not found. Installing dependencies..." -ForegroundColor Yellow
        py -m pip install -r requirements.txt
    } else {
        Write-Host "✅ Dependencies are installed." -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Installing dependencies..." -ForegroundColor Yellow
    py -m pip install -r requirements.txt
}

Write-Host ""
Write-Host "🗄️  Running migrations..." -ForegroundColor Cyan
Write-Host ""

# Run migrations
py manage.py migrate

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Database models created:" -ForegroundColor Cyan
    Write-Host "  - User (authentication)" -ForegroundColor White
    Write-Host "  - SMTPConfig (smtp_config)" -ForegroundColor White
    Write-Host "  - RecipientList, Recipient (recipients)" -ForegroundColor White
    Write-Host "  - Template (templates)" -ForegroundColor White
    Write-Host "  - Campaign (campaigns)" -ForegroundColor White
    Write-Host "  - EmailLog, EmailEvent (tracking)" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Task 1.3 Complete!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Migration failed. Please check the error messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. PostgreSQL not running - Start PostgreSQL service" -ForegroundColor White
    Write-Host "  2. Database not created - Run: createdb bulk_email_sender" -ForegroundColor White
    Write-Host "  3. Wrong credentials in .env - Check DB_USER, DB_PASSWORD, DB_HOST" -ForegroundColor White
    Write-Host ""
}
