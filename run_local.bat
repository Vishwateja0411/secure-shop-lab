@echo off
echo ===================================================
echo   SecureShop Lab - Local Launcher (No Docker Required)
echo ===================================================
echo.

IF NOT EXIST ".venv\Scripts\activate.bat" (
    echo Creating virtual environment in .venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r backend\requirements.txt

echo.
echo Starting SecureShop Lab at http://localhost:8000 ...
echo Open your browser at: http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
