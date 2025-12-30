# Camera System Setup Complete

## Summary

The camera system migration has been completed successfully. All code has been migrated from WatchTower (Flask) to the software project (FastAPI).

## What Was Done

✅ **Database Models** - Arlo and encoder models created  
✅ **Services** - ArloService and VideoEncoderService implemented  
✅ **API Routes** - FastAPI routers for camera and encoder endpoints  
✅ **Database Migrations** - Alembic migration created and tested  
✅ **Dependencies** - Core dependencies installed  
✅ **Configuration** - Environment variables documented  

## Current Status

### ✅ Completed
- All code migrated and adapted for FastAPI
- Database migrations created (tested with SQLite)
- API routers registered in main.py
- Environment variable setup script created

### ⚠️ Pending (Requires Setup)

1. **Arlo Library Installation**
   - The `arlo` library has encoding issues on Windows
   - Workaround: Local copy created at `services/camera/arlo_module.py`
   - For production: Use the workaround script or install on Linux

2. **Database Setup**
   - Migration tested with SQLite (for development)
   - **Production requires PostgreSQL**
   - Set `DATABASE_URL` environment variable

3. **Environment Variables**
   - Run `.\scripts\setup_camera_env.ps1` to set variables
   - **IMPORTANT**: Replace temporary secret keys with strong keys

4. **Authentication**
   - API endpoints require authentication
   - Get token: `POST /api/auth/token`
   - Use token: `Authorization: Bearer YOUR_TOKEN`

## Next Steps

### 1. Set Environment Variables
```powershell
cd d:\software
.\scripts\setup_camera_env.ps1
```

### 2. Start the Application
```powershell
python -m uvicorn app.main:app --reload
```

### 3. Test the API

**Get Authentication Token:**
```powershell
$body = @{
    username = "your_username"
    password = "your_password"
} | ConvertTo-Json

$token = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/token" -Method Post -Body $body -ContentType "application/json"
$headers = @{ "Authorization" = "Bearer $($token.access_token)" }
```

**List Cameras:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/camera/cameras" -Headers $headers
```

**Discover Cameras:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/camera/cameras/discover" -Method Post -Headers $headers
```

**List Encoders:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/encoder/encoders" -Headers $headers
```

## API Endpoints

### Camera Endpoints (`/api/camera`)
- `GET /api/camera/cameras` - List all cameras
- `GET /api/camera/cameras/{camera_id}` - Get camera details
- `POST /api/camera/cameras/discover` - Discover and register cameras
- `POST /api/camera/cameras/{camera_id}/arm` - Arm camera
- `POST /api/camera/cameras/{camera_id}/disarm` - Disarm camera
- `POST /api/camera/cameras/{camera_id}/snapshot` - Capture snapshot
- `GET /api/camera/cameras/{camera_id}/status` - Get camera status
- `GET /api/camera/cameras/{camera_id}/recordings` - List recordings
- `GET /api/camera/base-station` - Get base station info
- `POST /api/camera/cameras/{camera_id}/live-stream` - Start live stream

### Encoder Endpoints (`/api/encoder`)
- `GET /api/encoder/encoders` - List all encoders
- `GET /api/encoder/encoders/{encoder_id}` - Get encoder details
- `POST /api/encoder/encoders/discover` - Discover encoders
- `POST /api/encoder/encoders` - Register encoder
- `POST /api/encoder/encoders/{encoder_id}/record` - Start recording
- `POST /api/encoder/encoders/{encoder_id}/stop` - Stop recording
- `GET /api/encoder/encoders/{encoder_id}/status` - Get encoder status
- `POST /api/encoder/cameras/{camera_id}/record` - Record camera via encoder

## Troubleshooting

### Arlo Library Installation
If you encounter encoding errors:
- The local copy at `services/camera/arlo_module.py` should work
- For production, consider installing on Linux or using Docker

### Database Connection
- For development: SQLite works (already tested)
- For production: Use PostgreSQL and set `DATABASE_URL`

### Authentication
- All endpoints require authentication except `/api/camera/webhooks`
- Use OAuth2 token from `/api/auth/token`

## Files Created

- `app/models/camera/` - Camera database models
- `app/models/encoder/` - Encoder database models
- `services/camera/` - Camera service layer
- `services/video_encoder/` - Encoder service layer
- `app/api/camera.py` - Camera API router
- `app/api/encoder.py` - Encoder API router
- `alembic/versions/001_add_camera_and_encoder_tables.py` - Migration
- `scripts/setup_camera_env.ps1` - Environment setup script

## Architecture

```
Arlo Cameras → Arlo Service → AJA HELO Encoder → Local Storage/Media Server
```

The AJA HELO encoder serves as a recording backend for camera content.

