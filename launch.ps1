# Define the application directory
$appDirectory = "C:\Users\Sunny\Desktop\Repo\Talos\fastapi"

# Change to the app directory
Set-Location -Path $appDirectory

# Change the execution policy
Set-ExecutionPolicy Bypass -Scope Process -Force

# Activate the virtual environment
. .\venv\Scripts\Activate.ps1

# Launch the FastAPI server in a hidden window
Start-Process -WindowStyle Hidden -FilePath "powershell" -ArgumentList "uvicorn main:app --port 8567"
