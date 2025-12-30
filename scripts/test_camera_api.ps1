# PowerShell script to test camera API endpoints

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Camera API Integration Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
. .\scripts\setup_camera_env.ps1

Write-Host "Testing API endpoint availability..." -ForegroundColor Yellow

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Server is running on port 8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available endpoints:" -ForegroundColor Cyan
    Write-Host "  GET  /api/camera/cameras - List cameras" -ForegroundColor White
    Write-Host "  POST /api/camera/cameras/discover - Discover cameras" -ForegroundColor White
    Write-Host "  GET  /api/encoder/encoders - List encoders" -ForegroundColor White
    Write-Host "  POST /api/encoder/encoders/discover - Discover encoders" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: Endpoints require authentication. Use:" -ForegroundColor Yellow
    Write-Host "  curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:8000/api/camera/cameras" -ForegroundColor White
} catch {
    Write-Host "[WARNING] Server not running on port 8000" -ForegroundColor Yellow
    Write-Host "  -> Start server with: python -m uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host ""
    Write-Host "To test after starting server:" -ForegroundColor Cyan
    Write-Host "  1. Get auth token: POST /api/auth/token" -ForegroundColor White
    Write-Host "  2. Use token: GET /api/camera/cameras -H 'Authorization: Bearer TOKEN'" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

