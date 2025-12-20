# Raspberry Pi Device Setup Guide

## Overview

This guide explains how to set up and configure Raspberry Pi devices to work with the Educational System Service.

## Device Types

The service supports four types of Pi devices:

1. **Kiosk**: Display-only devices for viewing content
2. **Interactive**: Interactive learning stations
3. **Sync**: Devices for offline content synchronization
4. **IoT**: Devices with sensor data collection

## Initial Setup

### 1. Register Device

First, register your Pi device with the service:

```bash
curl -X POST http://education-service:8000/api/v1/pi/devices/register \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "pi-001",
    "device_name": "Classroom Display 1",
    "device_type": "kiosk",
    "organization_id": 1,
    "capabilities": {
      "display": true,
      "touch": false,
      "audio": true
    },
    "settings": {
      "display": {
        "resolution": "1920x1080",
        "orientation": "landscape"
      }
    }
  }'
```

### 2. Get Device Configuration

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001 \
  -H "Authorization: Bearer <token>"
```

## Content Synchronization

### Check for Updates

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/sync/check \
  -H "Authorization: Bearer <token>"
```

### Request Sync Package

```bash
curl -X POST "http://education-service:8000/api/v1/pi/devices/pi-001/sync/request?package_type=full" \
  -H "Authorization: Bearer <token>"
```

### Download Sync Package

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/sync/packages/1/download \
  -H "Authorization: Bearer <token>" \
  -o sync-package.tar.gz
```

### Mark Sync Complete

```bash
curl -X POST http://education-service:8000/api/v1/pi/devices/pi-001/sync/complete \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"package_id": 1}'
```

## Content Access

### Get Content List

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/content \
  -H "Authorization: Bearer <token>"
```

### Get Specific Content

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/content/123 \
  -H "Authorization: Bearer <token>"
```

### Get Display Configuration

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/display/config \
  -H "Authorization: Bearer <token>"
```

## IoT Sensor Integration

### Submit Sensor Data

```bash
curl -X POST http://education-service:8000/api/v1/pi/devices/pi-001/sensors/data \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_type": "temperature",
    "value": 22.5,
    "unit": "celsius",
    "timestamp": "2024-01-01T12:00:00Z",
    "metadata": {}
  }'
```

### Get Sensor Configuration

```bash
curl -X GET http://education-service:8000/api/v1/pi/devices/pi-001/sensors/config \
  -H "Authorization: Bearer <token>"
```

### Query Sensor Data

```bash
curl -X GET "http://education-service:8000/api/v1/pi/devices/pi-001/sensors/data?sensor_type=temperature" \
  -H "Authorization: Bearer <token>"
```

## Python Client Example

```python
import httpx
import asyncio

class PiClient:
    def __init__(self, base_url: str, token: str, device_id: str):
        self.base_url = base_url
        self.token = token
        self.device_id = device_id
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def check_updates(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/pi/devices/{self.device_id}/sync/check",
                headers=self.headers
            )
            return response.json()
    
    async def get_content(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/pi/devices/{self.device_id}/content",
                headers=self.headers
            )
            return response.json()

# Usage
client = PiClient("http://education-service:8000", "your-token", "pi-001")
updates = asyncio.run(client.check_updates())
```

## Offline Operation

For devices that need to work offline:

1. **Sync Content Before Going Offline**:
   - Request full sync package
   - Download and extract package
   - Store content locally

2. **Queue Activity Data**:
   - Store activity data locally when offline
   - Sync when connection is restored

3. **Incremental Sync**:
   - Use incremental sync packages for updates
   - Only download changed content

## Best Practices

1. **Regular Syncs**: Schedule regular sync checks
2. **Error Handling**: Implement retry logic for network failures
3. **Local Caching**: Cache frequently accessed content
4. **Battery Management**: For battery-powered devices, optimize sync frequency
5. **Security**: Store authentication tokens securely
6. **Monitoring**: Log device status and sync operations

## Troubleshooting

### Device Not Found

- Verify device is registered
- Check device_id is correct
- Ensure authentication token is valid

### Sync Failures

- Check network connectivity
- Verify device has sufficient storage
- Review sync package size limits
- Check device capabilities

### Content Not Loading

- Verify content exists
- Check device has access to organization
- Review content permissions
- Test API connectivity


