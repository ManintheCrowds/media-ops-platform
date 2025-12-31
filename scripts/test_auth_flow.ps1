# Test OAuth2 Authentication Flow
# This script tests the complete authentication flow: register, login, token validation

$baseUrl = "http://localhost:8000"
$headers = @{"Content-Type" = "application/json"}

Write-Host "Testing OAuth2 Authentication Flow..." -ForegroundColor Cyan

# Test 1: Register a new user
Write-Host "`n1. Testing user registration..." -ForegroundColor Yellow
$registerData = @{
    username = "testuser_$(Get-Random)"
    email = "test_$(Get-Random)@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method Post -Body $registerData -Headers $headers
    Write-Host "✅ User registered successfully: $($registerResponse.username)" -ForegroundColor Green
    $username = $registerResponse.username
} catch {
    Write-Host "❌ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "User may already exist, trying login instead..." -ForegroundColor Yellow
        $username = $registerData | ConvertFrom-Json | Select-Object -ExpandProperty username
    } else {
        exit 1
    }
}

# Test 2: Get OAuth2 token
Write-Host "`n2. Testing OAuth2 token endpoint..." -ForegroundColor Yellow
$loginData = @{
    username = $username
    password = "TestPassword123!"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/token" -Method Post -Body $loginData -ContentType "application/x-www-form-urlencoded"
    $token = $tokenResponse.access_token
    Write-Host "✅ Token obtained successfully" -ForegroundColor Green
    Write-Host "   Token type: $($tokenResponse.token_type)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Token request failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Get current user info with token
Write-Host "`n3. Testing /api/auth/me endpoint..." -ForegroundColor Yellow
$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $userInfo = Invoke-RestMethod -Uri "$baseUrl/api/auth/me" -Method Get -Headers $authHeaders
    Write-Host "✅ User info retrieved successfully" -ForegroundColor Green
    Write-Host "   Username: $($userInfo.username)" -ForegroundColor Gray
    Write-Host "   Email: $($userInfo.email)" -ForegroundColor Gray
    Write-Host "   Is Admin: $($userInfo.is_admin)" -ForegroundColor Gray
} catch {
    Write-Host "❌ User info request failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: Test invalid token
Write-Host "`n4. Testing invalid token rejection..." -ForegroundColor Yellow
$invalidHeaders = @{
    "Authorization" = "Bearer invalid_token_12345"
    "Content-Type" = "application/json"
}

try {
    Invoke-RestMethod -Uri "$baseUrl/api/auth/me" -Method Get -Headers $invalidHeaders
    Write-Host "❌ Invalid token was accepted (should have been rejected)" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✅ Invalid token correctly rejected (401 Unauthorized)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ All OAuth2 authentication tests passed!" -ForegroundColor Green

