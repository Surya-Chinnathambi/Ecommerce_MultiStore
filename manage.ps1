# E-Commerce Platform - Management Script
# Quick commands for development and deployment

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     E-Commerce Platform - Management Console              ║" -ForegroundColor Cyan
Write-Host "║     Full Stack + DevOps + Monitoring                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "Available Commands:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] Start All Services" -ForegroundColor Green
    Write-Host "  [2] Stop All Services" -ForegroundColor Red
    Write-Host "  [3] View Service Status" -ForegroundColor Cyan
    Write-Host "  [4] Run All Tests" -ForegroundColor Yellow
    Write-Host "  [5] View Logs (Backend)" -ForegroundColor Magenta
    Write-Host "  [6] View Logs (Frontend)" -ForegroundColor Magenta
    Write-Host "  [7] Restart Backend" -ForegroundColor Yellow
    Write-Host "  [8] Open Frontend in Browser" -ForegroundColor Cyan
    Write-Host "  [9] Open API Docs" -ForegroundColor Cyan
    Write-Host "  [10] Open Monitoring Dashboard" -ForegroundColor Cyan
    Write-Host "  [11] Clean Docker (Remove all containers & volumes)" -ForegroundColor Red
    Write-Host "  [12] Rebuild All Services" -ForegroundColor Yellow
    Write-Host "  [13] Backend Preflight Check" -ForegroundColor Yellow
    Write-Host "  [14] Bootstrap Backend Python Env" -ForegroundColor Yellow
    Write-Host "  [0] Exit" -ForegroundColor Gray
    Write-Host ""
}

function Start-AllServices {
    Write-Host "🚀 Starting all services..." -ForegroundColor Green
    docker compose up -d
    Start-Sleep -Seconds 5
    Write-Host "✅ Backend API:       http://localhost/api/docs" -ForegroundColor Green
    Write-Host "✅ Storefront:         http://localhost" -ForegroundColor Green
    Write-Host "✅ Database:           localhost:5432" -ForegroundColor Green
    Write-Host "✅ Redis:              localhost:6379" -ForegroundColor Green
}

function Stop-AllServices {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Red
    docker compose down
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor Cyan
    docker compose ps
}

function Run-AllTests {
    Write-Host "🧪 Running all tests..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "=== Backend Tests ==" -ForegroundColor Cyan
    docker-compose exec backend pytest tests/ -v --tb=short
    Write-Host ""
    Write-Host "✅ All tests completed" -ForegroundColor Green
}

function Show-BackendLogs {
    Write-Host "📜 Backend Logs (last 50 lines):" -ForegroundColor Magenta
    docker compose logs --tail=50 backend
}

function Show-FrontendLogs {
    Write-Host "📜 Storefront Logs:" -ForegroundColor Magenta
    docker compose logs -f storefront
}

function Restart-BackendService {
    Write-Host "🔄 Restarting backend..." -ForegroundColor Yellow
    docker compose restart backend
    Write-Host "✅ Backend restarted" -ForegroundColor Green
}

function Open-Frontend {
    Write-Host "🌐 Opening storefront in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost"
}

function Open-ApiDocs {
    Write-Host "📚 Opening API documentation..." -ForegroundColor Cyan
    Start-Process "http://localhost/api/docs"
}

function Open-Monitoring {
    Write-Host "📊 Opening Grafana monitoring dashboard..." -ForegroundColor Cyan
    Write-Host "Credentials: admin / admin (change via GRAFANA_ADMIN_PASSWORD env)" -ForegroundColor Yellow
    Start-Process "http://localhost:3000"
}

function Clean-Docker {
    Write-Host "⚠️  WARNING: This will remove all containers and volumes!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Host "🧹 Cleaning Docker..." -ForegroundColor Yellow
        docker compose down -v
        docker system prune -f
        Write-Host "✅ Docker cleaned" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Gray
    }
}

function Rebuild-Services {
    Write-Host "🔨 Rebuilding all services..." -ForegroundColor Yellow
    docker compose build --no-cache
    Write-Host "✅ Rebuild complete" -ForegroundColor Green
}

function Run-BackendPreflight {
    Write-Host "Running backend preflight checks..." -ForegroundColor Yellow
    if (Test-Path ".venv-backend\Scripts\python.exe") {
        & .\.venv-backend\Scripts\python.exe .\backend\scripts\preflight.py
        return
    }

    if (Test-Path ".venv\Scripts\python.exe") {
        & .\.venv\Scripts\python.exe .\backend\scripts\preflight.py
        return
    }

    Write-Host "Local virtual environment not found at .venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "Tip: run option 14 to bootstrap a compatible backend virtual environment." -ForegroundColor Yellow
}

function Bootstrap-BackendEnv {
    Write-Host "Bootstrapping backend Python environment..." -ForegroundColor Yellow
    & .\bootstrap_backend_env.ps1 -PythonVersion auto -VenvPath ".venv-backend"
}

# Main loop
do {
    Show-Menu
    $choice = Read-Host "Select an option"
    Write-Host ""
    
    switch ($choice) {
        "1" { Start-AllServices }
        "2" { Stop-AllServices }
        "3" { Show-Status }
        "4" { Run-AllTests }
        "5" { Show-BackendLogs }
        "6" { Show-FrontendLogs }
        "7" { Restart-BackendService }
        "8" { Open-Frontend }
        "9" { Open-ApiDocs }
        "10" { Open-Monitoring }
        "11" { Clean-Docker }
        "12" { Rebuild-Services }
        "13" { Run-BackendPreflight }
        "14" { Bootstrap-BackendEnv }
        "0" { 
            Write-Host "👋 Goodbye!" -ForegroundColor Cyan
            break
        }
        default { 
            Write-Host "❌ Invalid option" -ForegroundColor Red
        }
    }
    
    if ($choice -ne "0") {
        Write-Host ""
        Write-Host "Press Enter to continue..." -ForegroundColor Gray
        Read-Host
        Clear-Host
    }
} while ($choice -ne "0")
