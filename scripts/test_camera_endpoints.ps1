# PowerShell script to test camera API endpoints

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Camera API Endpoint Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
. .\scripts\setup_camera_env.ps1

Write-Host "Testing server connectivity..." -ForegroundColor Yellow

# Check if server is running
try {
    $apiInfo = Invoke-RestMethod -Uri "http://localhost:8000/api" -Method Get -TimeoutSec 5
    Write-Host "[OK] Server is running on port 8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available API endpoints:" -ForegroundColor Cyan
    $apiInfo.endpoints.PSObject.Properties | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
    }
    Write-Host ""
} catch {
    Write-Host "[ERROR] Server not responding on port 8000" -ForegroundColor Red
    Write-Host "  -> Start server with: python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host "Testing authentication..." -ForegroundColor Yellow

# Try to get a token (this will fail if no users exist, but that's OK for testing)
try {
    $tokenBody = @{
        username = "test"
        password = "test"
    } | ConvertTo-Json

    $token = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/token" -Method Post -Body $tokenBody -ContentType "application/json" -ErrorAction Stop
    $headers = @{ "Authorization" = "Bearer $($token.access_token)" }
    Write-Host "[OK] Authentication successful" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Testing camera endpoints..." -ForegroundColor Yellow
    
    # Test camera endpoints
    try {
        $cameras = Invoke-RestMethod -Uri "http://localhost:8000/api/camera/cameras" -Headers $headers -ErrorAction Stop
        Write-Host "[OK] GET /api/camera/cameras - Success" -ForegroundColor Green
        Write-Host "  Found $($cameras.Count) cameras" -ForegroundColor White
    } catch {
        Write-Host "[INFO] GET /api/camera/cameras - $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    try {
        $encoders = Invoke-RestMethod -Uri "http://localhost:8000/api/encoder/encoders" -Headers $headers -ErrorAction Stop
        Write-Host "[OK] GET /api/encoder/encoders - Success" -ForegroundColor Green
        Write-Host "  Found $($encoders.Count) encoders" -ForegroundColor White
    } catch {
        Write-Host "[INFO] GET /api/encoder/encoders - $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "[INFO] Authentication test failed (expected if no users exist)" -ForegroundColor Yellow
    Write-Host "  -> Create a user first via POST /api/auth/register" -ForegroundColor White
    Write-Host ""
    Write-Host "To test endpoints manually:" -ForegroundColor Cyan
    Write-Host "  1. Register user: POST /api/auth/register" -ForegroundColor White
    Write-Host "  2. Get token: POST /api/auth/token" -ForegroundColor White
    Write-Host "  3. Use token: GET /api/camera/cameras -H 'Authorization: Bearer TOKEN'" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

