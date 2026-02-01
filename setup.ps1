Write-Host " Starting PG Manager Setup..." -ForegroundColor Cyan

# 1. Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# 2. Setup Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host " Creating Python Virtual Environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host " Virtual Environment found." -ForegroundColor Green
}

# 3. Install Python Dependencies
Write-Host "⬇  Installing Python Dependencies..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install python requirements."; exit 1 }

# 4. Install Node Dependencies
if (Test-Path "package.json") {
    Write-Host "  Installing Node Dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install node modules."; exit 1 }
}

# 5. Initialize Database
Write-Host "  Initializing Database..." -ForegroundColor Yellow
# Run setup_db using the venv python to ensure psycopg2 is available
.\venv\Scripts\python.exe setup_db.py

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "To start the application, run:" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor Magenta
Write-Host "------------------------------------------------" -ForegroundColor Cyan
