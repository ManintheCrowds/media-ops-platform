# PowerShell script to start the FastAPI server with camera environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
. .\scripts\setup_camera_env.ps1

Write-Host "Starting server on http://localhost:8000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

