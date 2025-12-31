# Test Encoder API Endpoints
# This script tests all encoder endpoints after authentication

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Token = ""
)

if (-not $Token) {
    Write-Host "Error: Token required. Get token first using test_auth_flow.ps1" -ForegroundColor Red
    Write-Host "Usage: .\test_encoder_endpoints.ps1 -Token 'your_token_here'" -ForegroundColor Yellow
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

Write-Host "Testing Encoder API Endpoints..." -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Gray

# Test 1: List encoders
Write-Host "`n1. Testing GET /api/encoder/encoders (list encoders)..." -ForegroundColor Yellow
try {
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    Write-Host "✅ List encoders successful" -ForegroundColor Green
    Write-Host "   Found $($encoders.Count) encoders" -ForegroundColor Gray
} catch {
    Write-Host "❌ List encoders failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   (This is OK if no encoders are registered yet)" -ForegroundColor Yellow
    }
}

# Test 2: Discover encoders
Write-Host "`n2. Testing POST /api/encoder/encoders/discover..." -ForegroundColor Yellow
try {
    $discovered = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders/discover?network_range=192.168.1.0/24" -Method Post -Headers $headers
    Write-Host "✅ Encoder discovery successful" -ForegroundColor Green
    Write-Host "   Discovered $($discovered.discovered.Count) encoders" -ForegroundColor Gray
    if ($discovered.discovered.Count -gt 0) {
        $encoderId = $discovered.discovered[0].id
        Write-Host "   First encoder ID: $encoderId" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Encoder discovery failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   (This may fail if no encoders are on the network)" -ForegroundColor Yellow
}

# Test 3: Get specific encoder (if encoders exist)
Write-Host "`n3. Testing GET /api/encoder/encoders/{encoder_id}..." -ForegroundColor Yellow
try {
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    if ($encoders.Count -gt 0) {
        $encoderId = $encoders[0].id
        $encoder = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders/$encoderId" -Method Get -Headers $headers
        Write-Host "✅ Get encoder details successful" -ForegroundColor Green
        Write-Host "   Encoder: $($encoder.name)" -ForegroundColor Gray
        Write-Host "   Status: $($encoder.status)" -ForegroundColor Gray
        Write-Host "   IP: $($encoder.ip_address)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No encoders available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Get encoder failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Get encoder status (if encoders exist)
Write-Host "`n4. Testing GET /api/encoder/encoders/{encoder_id}/status..." -ForegroundColor Yellow
try {
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    if ($encoders.Count -gt 0) {
        $encoderId = $encoders[0].id
        $status = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders/$encoderId/status" -Method Get -Headers $headers
        Write-Host "✅ Get encoder status successful" -ForegroundColor Green
        Write-Host "   Status: $($status.status)" -ForegroundColor Gray
        Write-Host "   Recording: $($status.is_recording)" -ForegroundColor Gray
        Write-Host "   Streaming: $($status.is_streaming)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No encoders available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Get encoder status failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Start recording (if encoders exist)
Write-Host "`n5. Testing POST /api/encoder/encoders/{encoder_id}/record..." -ForegroundColor Yellow
try {
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    if ($encoders.Count -gt 0) {
        $encoderId = $encoders[0].id
        $recordData = @{
            source_url = "rtsp://test.example.com/stream"
            output_path = "/tmp/test_recording.mp4"
            duration = 60
        } | ConvertTo-Json
        $result = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders/$encoderId/record" -Method Post -Body $recordData -Headers $headers
        Write-Host "✅ Start recording successful" -ForegroundColor Green
        Write-Host "   Recording path: $($result.recording_path)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ No encoders available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Start recording failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Stop recording (if encoders exist)
Write-Host "`n6. Testing POST /api/encoder/encoders/{encoder_id}/stop..." -ForegroundColor Yellow
try {
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    if ($encoders.Count -gt 0) {
        $encoderId = $encoders[0].id
        $result = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders/$encoderId/stop" -Method Post -Headers $headers
        Write-Host "✅ Stop recording successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No encoders available to test" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Stop recording failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: Record camera via encoder (if cameras and encoders exist)
Write-Host "`n7. Testing POST /api/encoder/cameras/{camera_id}/record..." -ForegroundColor Yellow
try {
    # Check if cameras exist
    $cameras = Invoke-RestMethod -Uri "$BaseUrl/api/camera/cameras" -Method Get -Headers $headers
    $encoders = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/encoders" -Method Get -Headers $headers
    
    if ($cameras.Count -gt 0 -and $encoders.Count -gt 0) {
        $cameraId = $cameras[0].id
        $encoderId = $encoders[0].id
        $result = Invoke-RestMethod -Uri "$BaseUrl/api/encoder/cameras/$cameraId/record?encoder_id=$encoderId" -Method Post -Headers $headers
        Write-Host "✅ Camera recording via encoder successful" -ForegroundColor Green
        Write-Host "   Recording ID: $($result.recording_id)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ Need both cameras and encoders to test this endpoint" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Camera recording via encoder failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ Encoder endpoint tests completed!" -ForegroundColor Green
Write-Host "Note: Some tests may fail if encoders are not available on the network" -ForegroundColor Gray

