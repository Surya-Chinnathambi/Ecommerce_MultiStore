@echo off
setlocal

echo ============================================
echo  Docker Desktop - Force Reinstall
echo  Run this as Administrator!
echo ============================================
echo.

:: Verify we have admin rights
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)
echo [OK] Running with administrator rights.

:: Step 1: Stop Docker if running
echo.
echo [1/5] Stopping any running Docker processes...
taskkill /F /IM "Docker Desktop.exe" /T >nul 2>&1
taskkill /F /IM "dockerd.exe" /T >nul 2>&1
taskkill /F /IM "docker.exe" /T >nul 2>&1
echo       Done.

:: Step 2: Remove stale phantom registry entry (this is why installer says "up to date")
echo.
echo [2/5] Removing stale Docker registry entries...
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop" /f >nul 2>&1
echo       Done.

:: Step 3: Clean up phantom empty install folder
echo.
echo [3/5] Cleaning phantom install folder...
if exist "C:\Program Files\Docker\Docker\" (
    rmdir /S /Q "C:\Program Files\Docker\Docker\" >nul 2>&1
)
if exist "C:\Program Files\Docker\" (
    rmdir "C:\Program Files\Docker\" >nul 2>&1
)
echo       Done.

:: Step 4: Locate installer
echo.
echo [4/5] Preparing installer...

:: Copy installer to a path without spaces
copy /Y "%TEMP%\DockerDesktopInstaller.exe" "%USERPROFILE%\docker_setup.exe" >nul 2>&1
if not exist "%USERPROFILE%\docker_setup.exe" (
    echo ERROR: Installer not found at %%TEMP%%\DockerDesktopInstaller.exe
    echo Please download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo       Done.

:: Step 5: Run installer — registry is now clean so it will do a fresh install
echo.
echo [5/5] Running fresh Docker Desktop install (may take several minutes)...
echo.
"%USERPROFILE%\docker_setup.exe" install --accept-license --quiet

set EXIT_CODE=%ERRORLEVEL%
del "%USERPROFILE%\docker_setup.exe" >nul 2>&1

echo.
if %EXIT_CODE% == 0 (
    echo ============================================
    echo  SUCCESS! Docker Desktop installed.
    echo ============================================
    echo.
    echo Next steps:
    echo  1. RESTART your PC
    echo  2. Launch Docker Desktop from the Start Menu
    echo  3. Wait for the whale icon in the system tray
    echo  4. Then open a terminal and run:
    echo     cd C:\ecommerce-platform
    echo     docker compose -f docker-compose.dev.yml up --build
    echo.
) else (
    echo ============================================
    echo  ERROR: Exit code %EXIT_CODE%
    echo ============================================
    echo.
    echo Check log: C:\Users\%USERNAME%\AppData\Local\Docker\install-log.txt
    echo.
)
pause
