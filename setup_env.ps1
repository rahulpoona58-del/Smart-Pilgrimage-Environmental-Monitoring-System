# PowerShell Environment Setup Script for SPEMS Local Prototype
# Run this inside VS Code PowerShell terminal: .\setup_env.ps1

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "SPEMS - Local Environment Initialization (Windows)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Create virtual environment
if (-not (Test-Path -Path "venv")) {
    Write-Host "[1/3] Creating Python Virtual Environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment successfully created." -ForegroundColor Green
} else {
    Write-Host "[1/3] Virtual environment already exists. Skipping creation." -ForegroundColor Gray
}

# 2. Activate virtual environment and upgrade pip
Write-Host "[2/3] Upgrading pip Package Manager..." -ForegroundColor Yellow
& .\venv\Scripts\pip.exe install --upgrade pip
Write-Host "pip successfully upgraded." -ForegroundColor Green

# 3. Install required open-source CV libraries
Write-Host "[3/3] Installing Python Dependencies from requirements.txt..." -ForegroundColor Yellow
& .\venv\Scripts\pip.exe install -r requirements.txt
Write-Host "Dependencies successfully installed." -ForegroundColor Green

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Initialization complete. Run: '.\venv\Scripts\Activate.ps1'" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
