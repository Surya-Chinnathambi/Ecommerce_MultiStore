#!/usr/bin/env pwsh
param(
    [ValidateSet("auto", "3.11", "3.12", "3.13")]
    [string]$PythonVersion = "auto",
    [string]$VenvPath = ".venv-backend",
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"

function Find-PythonExecutable {
    param([string]$Version)

    $candidates = @()
    if ($Version -eq "auto") {
        $candidates = @("3.11", "3.12", "3.13")
    } else {
        $candidates = @($Version)
    }

    foreach ($ver in $candidates) {
        try {
            $exe = py -$ver -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) {
                return $exe.Trim()
            }
        } catch {
            # continue scanning
        }
    }

    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $null
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Backend Python Environment Bootstrap" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

$pythonExe = Find-PythonExecutable -Version $PythonVersion
if (-not $pythonExe) {
    Write-Host "No compatible Python found (needs 3.11, 3.12, or 3.13)." -ForegroundColor Red
    Write-Host "Install Python 3.11, then re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Green

if (Test-Path $VenvPath) {
    if (-not $Recreate) {
        Write-Host "Virtual environment already exists at $VenvPath" -ForegroundColor Yellow
        Write-Host "Re-run with -Recreate to rebuild it." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Removing existing virtual environment at $VenvPath" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvPath
}

Write-Host "Creating virtual environment at $VenvPath" -ForegroundColor Yellow
& $pythonExe -m venv $VenvPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment." -ForegroundColor Red
    exit 1
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment python was not created at $venvPython" -ForegroundColor Red
    exit 1
}

Write-Host "Upgrading pip" -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upgrade pip." -ForegroundColor Red
    exit 1
}

Write-Host "Installing backend requirements" -ForegroundColor Yellow
& $venvPython -m pip install -r .\backend\requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dependency install failed." -ForegroundColor Red
    Write-Host "Tip: Python 3.11 is recommended for best compatibility." -ForegroundColor Yellow
    exit 1
}

Write-Host "Running backend preflight" -ForegroundColor Yellow
& $venvPython .\backend\scripts\preflight.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Preflight failed after setup." -ForegroundColor Red
    exit 1
}

Write-Host "" 
Write-Host "Backend environment is ready." -ForegroundColor Green
Write-Host "Activate with: .\\$VenvPath\\Scripts\\Activate.ps1" -ForegroundColor Cyan
