# OAuth2 Fix and Server Setup Complete

## ✅ OAuth2 Compatibility Issue Fixed

### Problem
- **Error**: `AttributeError: 'FieldInfo' object has no attribute 'in_'`
- **Cause**: FastAPI 0.104.1 incompatible with Pydantic 2.12.5
- **Location**: `app/auth/oauth2.py` when processing `OAuth2PasswordRequestForm`

### Solution
- **Upgraded FastAPI**: 0.104.1 → 0.128.0
- **Updated requirements.txt**: Changed FastAPI version constraint
- **Result**: All imports now work successfully

### Verification
```powershell
✅ API routers imported successfully
✅ FastAPI app imported successfully
✅ App created with 55 routes
   - 15 camera routes
   - 8 encoder routes
```

## 🚀 Server Startup

### Quick Start
```powershell
cd d:\software
.\scripts\start_server.ps1
```

Or manually:
```powershell
cd d:\software
.\scripts\setup_camera_env.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Server Status
- **Port**: 8000
- **Host**: 0.0.0.0 (all interfaces)
- **Reload**: Enabled (auto-reload on code changes)
- **Routes**: 55 total routes registered

## 🧪 Testing Endpoints

### 1. Check Server Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api" -Method Get
```

### 2. Create a User (First Time)
```powershell
$userData = @{
    username = "admin"
    email = "admin@example.com"
    password = "SecurePassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method Post -Body $userData -ContentType "application/json"
```

### 3. Get Authentication Token
```powershell
$loginData = @{
    username = "admin"
    password = "SecurePassword123!"
} | ConvertTo-Json

$token = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/token" -Method Post -Body $loginData -ContentType "application/x-www-form-urlencoded"
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }
```

### 4. Test Camera Endpoints
```powershell
# List cameras
Invoke-RestMethod -Uri "http://localhost:8000/api/camera/cameras" -Headers $headers

# Discover cameras
Invoke-RestMethod -Uri "http://localhost:8000/api/camera/cameras/discover" -Method Post -Headers $headers

# Get base station info
Invoke-RestMethod -Uri "http://localhost:8000/api/camera/base-station" -Headers $headers
```

### 5. Test Encoder Endpoints
```powershell
# List encoders
Invoke-RestMethod -Uri "http://localhost:8000/api/encoder/encoders" -Headers $headers

# Discover encoders
Invoke-RestMethod -Uri "http://localhost:8000/api/encoder/encoders/discover" -Method Post -Headers $headers -Body (@{network_range="192.168.1.0/24"} | ConvertTo-Json) -ContentType "application/json"
```

## 📋 Available Endpoints

### Camera Endpoints (`/api/camera`)
- `GET /api/camera/cameras` - List all cameras
- `GET /api/camera/cameras/{camera_id}` - Get camera details
- `POST /api/camera/cameras/discover` - Discover and register cameras
- `POST /api/camera/cameras/{camera_id}/arm` - Arm camera
- `POST /api/camera/cameras/{camera_id}/disarm` - Disarm camera
- `POST /api/camera/cameras/{camera_id}/snapshot` - Capture snapshot
- `GET /api/camera/cameras/{camera_id}/status` - Get camera status
- `GET /api/camera/cameras/{camera_id}/recordings` - List recordings
- `GET /api/camera/cameras/{camera_id}/recordings/{recording_id}/download` - Download recording
- `DELETE /api/camera/cameras/{camera_id}/recordings/{recording_id}` - Delete recording
- `GET /api/camera/base-station` - Get base station info
- `POST /api/camera/cameras/{camera_id}/live-stream` - Start live stream
- `POST /api/camera/scan-network` - Scan network for base stations
- `POST /api/camera/webhooks` - Arlo webhook endpoint

### Encoder Endpoints (`/api/encoder`)
- `GET /api/encoder/encoders` - List all encoders
- `GET /api/encoder/encoders/{encoder_id}` - Get encoder details
- `POST /api/encoder/encoders/discover` - Discover encoders
- `POST /api/encoder/encoders` - Register encoder
- `POST /api/encoder/encoders/{encoder_id}/record` - Start recording
- `POST /api/encoder/encoders/{encoder_id}/stop` - Stop recording
- `GET /api/encoder/encoders/{encoder_id}/status` - Get encoder status
- `POST /api/encoder/cameras/{camera_id}/record` - Record camera via encoder

## 🔧 Environment Variables

Required environment variables (set by `scripts/setup_camera_env.ps1`):

```powershell
# Required Secrets
$env:SECRET_KEY = "your_32_char_secret_key"
$env:JWT_SECRET_KEY = "your_32_char_jwt_secret"

# Database
$env:DATABASE_URL = "sqlite:///./test_platform.db"  # or PostgreSQL URL

# Arlo Configuration
$env:ARLO_USERNAME = "your@email.com"
$env:ARLO_PASSWORD = "your_password"
$env:ARLO_STORAGE_PATH = "D:\portfolio-harness\software\camera_recordings"
$env:ARLO_SYNC_INTERVAL = "300"
$env:ARLO_ENCRYPTION_KEY = "your_encryption_key"
```

## ✅ Verification Checklist

- [x] OAuth2 compatibility issue fixed
- [x] FastAPI upgraded to 0.128.0
- [x] All imports working
- [x] App creates successfully (55 routes)
- [x] Camera routes registered (15 endpoints)
- [x] Encoder routes registered (8 endpoints)
- [x] Environment setup script created
- [x] Server startup script created
- [x] Test script created

## 🎯 Next Steps

1. **Start the server:**
   ```powershell
   .\scripts\start_server.ps1
   ```

2. **Create a user** (if not exists):
   ```powershell
   # Use the register endpoint
   ```

3. **Test camera discovery:**
   ```powershell
   # POST /api/camera/cameras/discover
   ```

4. **Test encoder discovery:**
   ```powershell
   # POST /api/encoder/encoders/discover
   ```

5. **Record a camera:**
   ```powershell
   # POST /api/encoder/cameras/{camera_id}/record?encoder_id={encoder_id}
   ```

## 📝 Notes

- **Database**: Currently using SQLite for testing. Production should use PostgreSQL.
- **Authentication**: All endpoints (except webhooks) require authentication.
- **CORS**: Configure `CORS_ORIGINS` environment variable if needed for frontend access.
- **Arlo Library**: Using local fallback due to Windows encoding issues.

## 🐛 Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify environment variables are set
- Check database connection (if using PostgreSQL)

### Authentication fails
- Verify user exists in database
- Check JWT_SECRET_KEY is set correctly
- Ensure password is correct

### Camera discovery fails
- Verify ARLO_USERNAME and ARLO_PASSWORD are correct
- Check Arlo base station is online
- Ensure base station is registered to the account

### Encoder discovery fails
- Check network connectivity
- Verify encoder is on the network
- Check firewall settings

