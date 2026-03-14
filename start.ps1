# E-Commerce Platform - Quick Start Script
# Run this in PowerShell to start the platform

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   E-Commerce Platform - Quick Start                        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerRunning = $false
try {
    $dockerVersion = docker version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "✓ Docker is running" -ForegroundColor Green
    }
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "✗ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Navigate to project directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Backend preflight for local Python environments
if (Test-Path ".venv-backend\Scripts\python.exe") {
    Write-Host "Running backend preflight checks..." -ForegroundColor Yellow
    & .\.venv-backend\Scripts\python.exe .\backend\scripts\preflight.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Preflight reported issues. Continuing with Docker startup." -ForegroundColor Yellow
        Write-Host "Use manage.ps1 option 13 for strict local backend validation." -ForegroundColor Yellow
    } else {
        Write-Host "✓ Backend preflight passed" -ForegroundColor Green
    }
    Write-Host ""
} elseif (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "Running backend preflight checks..." -ForegroundColor Yellow
    & .\.venv\Scripts\python.exe .\backend\scripts\preflight.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Preflight reported issues. Continuing with Docker startup." -ForegroundColor Yellow
        Write-Host "Use manage.ps1 option 13 for strict local backend validation." -ForegroundColor Yellow
    } else {
        Write-Host "✓ Backend preflight passed" -ForegroundColor Green
    }
    Write-Host ""
} else {
    Write-Host "Skipping local preflight (.venv not found)." -ForegroundColor Gray
    Write-Host ""
}

# Check if .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "Creating backend/.env from template..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✓ Created backend/.env" -ForegroundColor Green
    Write-Host ""
}

# Start services
Write-Host "Starting services with Docker Compose..." -ForegroundColor Yellow
Write-Host "(This may take 2-3 minutes on first run)" -ForegroundColor Gray
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Services started successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check service status
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   Services are running!                                    " -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Initialize database
    Write-Host "Would you like to initialize the database with demo data? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host ""
        Write-Host "Initializing database..." -ForegroundColor Yellow
        docker-compose exec -T backend python scripts/init_db.py
        Write-Host ""
    }
    
    # Display access URLs
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   Access the Platform                                      " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "API Documentation:  " -NoNewline
    Write-Host "http://localhost:8000/api/docs" -ForegroundColor Green
    Write-Host "Health Check:       " -NoNewline
    Write-Host "http://localhost:8000/health" -ForegroundColor Green
    Write-Host "Celery Flower:      " -NoNewline
    Write-Host "http://localhost:5555" -ForegroundColor Green
    Write-Host "RabbitMQ Mgmt:      " -NoNewline
    Write-Host "http://localhost:15672" -ForegroundColor Green
    Write-Host "                    (user: ecommerce, pass: ecommerce_queue_pass)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   Useful Commands                                          " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "View logs:          " -NoNewline
    Write-Host "docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "View backend logs:  " -NoNewline
    Write-Host "docker-compose logs -f backend" -ForegroundColor Yellow
    Write-Host "Stop services:      " -NoNewline
    Write-Host "docker-compose down" -ForegroundColor Yellow
    Write-Host "Restart service:    " -NoNewline
    Write-Host "docker-compose restart backend" -ForegroundColor Yellow
    Write-Host ""
    
    # Open browser
    Write-Host "Would you like to open the API documentation in your browser? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Start-Process "http://localhost:8000/api/docs"
    }
    
    Write-Host ""
    Write-Host "Platform started successfully! Happy coding! 🚀" -ForegroundColor Green
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "✗ Failed to start services!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure Docker Desktop is running" -ForegroundColor Gray
    Write-Host "2. Check if ports 5432, 6379, 8000, 5555 are available" -ForegroundColor Gray
    Write-Host "3. Run: docker-compose logs" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Press Enter to exit..."
Read-Host
