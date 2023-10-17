Set-ExecutionPolicy Bypass -Scope Process -Force
$appDirectory = "C:\Users\Sunny\Desktop\Repo\Talos\fastapi"
Set-Location -Path $appDirectory

py -3 -m venv venv
. .\venv\Scripts\Activate.ps1
pip install -r requirements.txt