# Test Camera API Endpoints
# This script tests all camera endpoints after authentication

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Token = ""
)

if (-not $Token) {
    Write-Host "Error: Token required. Get token first using test_auth_flow.ps1" -ForegroundColor Red
    Write-Host "Usage: .\test_camera_endpoints.ps1 -Token 'your_token_here'" -ForegroundColor Yellow
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

Write-Host "Testing Camera API Endpoints..." -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Gray

# Test 1: List cameras
Write-Host "`n1. Testing GET /api/camera/cameras (list cameras)..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    Write-Host "✅ List cameras successful" -ForegroundColor Green
    Write-Host "   Found $($cameras.Count) cameras" -ForegroundColor Gray
} catch {
    Write-Host "❌ List cameras failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   (This is OK if no cameras are registered yet)" -ForegroundColor Yellow
    }
}

# Test 2: Discover cameras
Write-Host "`n2. Testing POST /api/camera/cameras/discover..." -ForegroundColor Yellow
try {
    $discovered = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/discover" -Method Post -Headers $headers
    Write-Host "✅ Camera discovery successful" -ForegroundColor Green
    Write-Host "   Discovered $($discovered.Count) cameras" -ForegroundColor Gray
    if ($discovered.Count -gt 0) {
        $cameraId = $discovered[0].id
        Write-Host "   First camera ID: $cameraId" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Camera discovery failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   (This may fail if Arlo credentials are not configured)" -ForegroundColor Yellow
}

# Test 3: Get base station info
Write-Host "`n3. Testing GET /api/camera/base-station..." -ForegroundColor Yellow
try {
    $baseStation = Invoke-RestMethod -Uri "$BaseUrl/api/camera/base-station" -Method Get -Headers $headers
    Write-Host "✅ Base station info retrieved" -ForegroundColor Green
    Write-Host "   Name: $($baseStation.name)" -ForegroundColor Gray
    Write-Host "   Status: $($baseStation.status)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Base station info failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   (This may fail if Arlo is not configured)" -ForegroundColor Yellow
}

# Test 4: Get specific camera (if cameras exist)
Write-Host "`n4. Testing GET /api/camera/cameras/{camera_id}..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $camera = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId" -Method Get -Headers $headers
        Write-Host "✅ Get camera details successful" -ForegroundColor Green
        Write-Host "   Camera: $($camera.name)" -ForegroundColor Gray
        Write-Host "   Status: $($camera.status)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Get camera failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Get camera status (if cameras exist)
Write-Host "`n5. Testing GET /api/camera/cameras/{camera_id}/status..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $status = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId/status" -Method Get -Headers $headers
        Write-Host "✅ Get camera status successful" -ForegroundColor Green
        Write-Host "   Status: $($status.status)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Get camera status failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Arm camera (if cameras exist)
Write-Host "`n6. Testing POST /api/camera/cameras/{camera_id}/arm..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $result = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId/arm" -Method Post -Headers $headers
        Write-Host "✅ Arm camera successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Arm camera failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: Disarm camera (if cameras exist)
Write-Host "`n7. Testing POST /api/camera/cameras/{camera_id}/disarm..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $result = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId/disarm" -Method Post -Headers $headers
        Write-Host "✅ Disarm camera successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Disarm camera failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: Capture snapshot (if cameras exist)
Write-Host "`n8. Testing POST /api/camera/cameras/{camera_id}/snapshot..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $snapshot = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId/snapshot" -Method Post -Headers $headers
        Write-Host "✅ Snapshot capture successful" -ForegroundColor Green
        Write-Host "   Snapshot URL: $($snapshot.snapshot_url)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Snapshot capture failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 9: List recordings (if cameras exist)
Write-Host "`n9. Testing GET /api/camera/cameras/{camera_id}/recordings..." -ForegroundColor Yellow
try {
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    if ($cameras.Count -gt 0) {
        $cameraId = $cameras[0].id
        $recordings = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras/$cameraId/recordings" -Method Get -Headers $headers
        Write-Host "✅ List recordings successful" -ForegroundColor Green
        Write-Host "   Found $($recordings.Count) recordings" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No cameras available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ List recordings failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ Camera endpoint tests completed!" -ForegroundColor Green
Write-Host "Note: Some tests may fail if Arlo is not configured or cameras are not available" -ForegroundColor Gray
