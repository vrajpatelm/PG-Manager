# Run the Flask app using the venv python (Windows PowerShell)
$env:FLASK_APP = 'run.py'
$env:FLASK_ENV = 'development'
.\venv\Scripts\python.exe -m flask run
