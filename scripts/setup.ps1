# Create a virtual environment and install requirements (Windows PowerShell)
python -m venv venv
# Use the venv python to install without needing to activate
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Virtual environment created and packages installed. To activate, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Green
