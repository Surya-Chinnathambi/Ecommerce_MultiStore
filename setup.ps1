#!/usr/bin/env pwsh
# Complete setup automation for E-Commerce Platform

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "E-Commerce Platform - Complete Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Starting Backend Services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Step 2: Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "Step 3: Initializing database..." -ForegroundColor Yellow
docker-compose exec backend python scripts/init_db.py

Write-Host ""
Write-Host "Step 4: Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend/storefront
npm install
Set-Location ../..

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are ready:" -ForegroundColor Cyan
Write-Host "  Backend API:     http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "  Frontend:        http://localhost:5173?store_id=STORE001" -ForegroundColor White
Write-Host "  Flower Monitor:  http://localhost:5555" -ForegroundColor White
Write-Host "  RabbitMQ:        http://localhost:15672 (guest/guest)" -ForegroundColor White
Write-Host ""
Write-Host "To start the frontend development server:" -ForegroundColor Yellow
Write-Host "  cd frontend/storefront" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
