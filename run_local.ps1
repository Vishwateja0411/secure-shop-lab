Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  SecureShop Lab - Local Launcher (No Docker Needed)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

if (-Not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing required dependencies..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

Write-Host "`nStarting SecureShop Lab on http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "Open http://localhost:8000 in your browser to start hacking and learning!" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate the server.`n" -ForegroundColor DarkGray

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
