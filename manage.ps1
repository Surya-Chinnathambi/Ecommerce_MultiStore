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
    Write-Host "  [0] Exit" -ForegroundColor Gray
    Write-Host ""
}

function Start-AllServices {
    Write-Host "🚀 Starting all services..." -ForegroundColor Green
    docker-compose up -d
    Start-Sleep -Seconds 5
    Write-Host "✅ Backend running on http://localhost:8000" -ForegroundColor Green
    Write-Host "✅ Database running on localhost:5432" -ForegroundColor Green
    Write-Host "✅ Redis running on localhost:6379" -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting frontend..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend\storefront; npm run dev"
    Write-Host "✅ Frontend running on http://localhost:3000" -ForegroundColor Green
}

function Stop-AllServices {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Red
    docker-compose down
    Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor Cyan
    docker-compose ps
    Write-Host ""
    Write-Host "Frontend Status:" -ForegroundColor Cyan
    $nodeProcess = Get-Process -Name node -ErrorAction SilentlyContinue
    if ($nodeProcess) {
        Write-Host "✅ Frontend running (PID: $($nodeProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend not running" -ForegroundColor Red
    }
}

function Run-AllTests {
    Write-Host "🧪 Running all tests..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "=== Backend API Tests ===" -ForegroundColor Cyan
    python backend\test_api.py
    Write-Host ""
    Write-Host "=== New Features Tests ===" -ForegroundColor Cyan
    python test_new_features.py
    Write-Host ""
    Write-Host "✅ All tests completed" -ForegroundColor Green
}

function Show-BackendLogs {
    Write-Host "📜 Backend Logs (last 50 lines):" -ForegroundColor Magenta
    docker-compose logs --tail=50 backend
}

function Show-FrontendLogs {
    Write-Host "📜 Starting frontend log viewer..." -ForegroundColor Magenta
    docker-compose logs -f frontend
}

function Restart-BackendService {
    Write-Host "🔄 Restarting backend..." -ForegroundColor Yellow
    docker-compose restart backend
    Write-Host "✅ Backend restarted" -ForegroundColor Green
}

function Open-Frontend {
    Write-Host "🌐 Opening frontend in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000"
}

function Open-ApiDocs {
    Write-Host "📚 Opening API documentation..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/docs"
}

function Open-Monitoring {
    Write-Host "📊 Opening monitoring dashboard..." -ForegroundColor Cyan
    Write-Host "Note: Login required (admin@test.com / admin123)" -ForegroundColor Yellow
    Start-Process "http://localhost:3000/monitoring"
}

function Clean-Docker {
    Write-Host "⚠️  WARNING: This will remove all containers and volumes!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -eq "yes") {
        Write-Host "🧹 Cleaning Docker..." -ForegroundColor Yellow
        docker-compose down -v
        docker system prune -f
        Write-Host "✅ Docker cleaned" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Gray
    }
}

function Rebuild-Services {
    Write-Host "🔨 Rebuilding all services..." -ForegroundColor Yellow
    docker-compose build --no-cache
    Write-Host "✅ Rebuild complete" -ForegroundColor Green
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
