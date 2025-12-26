# Raspberry Pi Client for Educational Platform

A lightweight standalone Python application for Raspberry Pi devices to connect to the educational platform for content streaming, display management, and local interaction.

## Features

- **Lightweight API Client**: Efficient HTTP client with automatic retry and token refresh
- **Local Caching**: LRU cache with TTL support for offline operation
- **Content Streaming**: HTTP range request streaming with adaptive quality
- **Display Management**: Web-based UI with content rotation and multiple display modes
- **Hardware Integration**: GPIO, camera, audio, and power management support
- **Security**: Certificate-based authentication, encryption, and remote wipe capability
- **Offline Support**: Background sync with package download and extraction

## Installation

### Prerequisites

- Raspberry Pi OS (Bullseye or later)
- Python 3.9+
- Network connectivity
- Minimum 8GB free storage

### Quick Install

```bash
git clone <repository>
cd pi-client
./scripts/install.sh
./scripts/setup.sh
sudo systemctl start pi-client
sudo systemctl enable pi-client
```

## Configuration

Configuration is stored in `/etc/pi-client/config.yaml`. See the setup script for interactive configuration, or edit the file directly.

Example configuration:

```yaml
device:
  device_id: "pi-001"
  device_name: "Classroom Display 1"

api:
  base_url: "https://education.example.com"
  auth_token: "your-token-here"

cache:
  directory: "/home/pi/.pi-client/cache"
  max_size_mb: 5000
  ttl_hours: 168

display:
  port: 8080
  rotation: "landscape"
  fullscreen: true
  mode: "kiosk"

hardware:
  gpio_enabled: true
  camera_enabled: false
  audio_enabled: true

security:
  cert_path: "/etc/pi-client/certs/device.pem"
  encryption_enabled: true
```

## Usage

### Running the Client

```bash
# As systemd service (recommended)
sudo systemctl start pi-client
sudo systemctl status pi-client

# Manually
python -m pi_client.main --config /etc/pi-client/config.yaml
```

### Accessing the Web UI

Once running, access the web UI at `http://<pi-ip>:8080`

- Dashboard: `http://<pi-ip>:8080/`
- Content Browser: `http://<pi-ip>:8080/content`
- Settings: `http://<pi-ip>:8080/settings`

## Hardware Integration

See [HARDWARE_GUIDE.md](docs/HARDWARE_GUIDE.md) for detailed hardware integration examples.

### GPIO Example

```python
from pi_client.hardware.gpio import GPIOInterface

gpio = GPIOInterface()
gpio.setup_pin(18, PinMode.OUTPUT)
gpio.write_pin(18, True)  # Turn on LED
```

### Camera Example

```python
from pi_client.hardware.camera import CameraInterface

camera = CameraInterface()
photo_path = camera.capture_photo("/tmp/photo.jpg")
```

### Audio Example

```python
from pi_client.hardware.audio import AudioManager

audio = AudioManager()
audio.play_file("/path/to/audio.mp3", volume=0.8)
```

## Platform Integration

The Pi client integrates with the education service and main platform:

- **Education Service Connection**: Primary API endpoint for content and sync
- **Platform Authentication**: Uses platform JWT tokens for authentication
- **Device Registration**: Registers device with education service
- **Health Monitoring**: Reports device status to platform monitoring

### Authentication Flow

1. **Device Registration**: Pi device registers with education service
   - Device ID and certificate generated
   - Device registered in education service database
   - Initial authentication token received

2. **Token Refresh**: Tokens automatically refreshed
   - Client requests new token before expiration
   - Uses device certificate for authentication
   - Seamless token rotation

3. **API Requests**: All API requests use JWT tokens
   - Token included in Authorization header
   - Automatic retry on authentication failures
   - Token refresh on 401 responses

### Device Registration Process

1. Generate device certificate (if not exists)
2. Register device with education service:
   ```bash
   curl -X POST https://education.example.com/api/v1/pi/devices/register \
     -H "Content-Type: application/json" \
     -d '{
       "device_id": "pi-001",
       "device_name": "Classroom Display 1",
       "certificate": "<certificate-data>"
     }'
   ```
3. Receive authentication token
4. Store token in device configuration
5. Start syncing content

## API Integration

The client communicates with the education service API at `/api/v1/pi`. See the [Education Service README](../education-service/README.md) for API details.

**Key Endpoints:**
- `GET /api/v1/pi/content` - Get content list for Pi
- `GET /api/v1/pi/content/{id}` - Download content package
- `POST /api/v1/pi/sync` - Sync progress from device
- `GET /api/v1/pi/devices/{device_id}` - Get device status

## Security

- Certificate-based authentication
- TLS/SSL for all communications
- Encrypted local cache (optional)
- Remote wipe capability

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u pi-client -f

# Check configuration
sudo pi-client --config /etc/pi-client/config.yaml --validate
```

### Cache issues

```bash
# Clear cache
rm -rf ~/.pi-client/cache/*

# Check cache size
du -sh ~/.pi-client/cache
```

### Network issues

```bash
# Test API connectivity
curl -H "Authorization: Bearer <token>" https://education.example.com/api/v1/pi/devices/<device_id>
```

## Deployment

### Automated Deployment (Ansible)

Use Ansible playbook for automated deployment:

```bash
ansible-playbook ../ansible/playbooks/pi-provision.yml -i pi-001,
```

The playbook handles:
- OS preparation and updates
- Pi client installation
- Certificate generation
- Service configuration
- Device registration
- Systemd service setup

### Manual Setup

1. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv
   ```

2. **Install Pi client:**
   ```bash
   pip3 install -r requirements.txt
   pip3 install -e .
   ```

3. **Configure service:**
   ```bash
   sudo ./scripts/setup.sh
   ```

4. **Start service:**
   ```bash
   sudo systemctl start pi-client
   sudo systemctl enable pi-client
   ```

### Deployment Comparison

**Ansible (Recommended):**
- Automated and repeatable
- Handles all configuration
- Includes device registration
- Best for multiple devices

**Manual Setup:**
- More control over process
- Good for single device
- Useful for development
- Requires manual configuration

## Related Services

- [Education Service](../education-service/README.md) - Educational platform integration
- [Platform API](../README.md) - Main integration layer
- [Ansible Automation](../ansible/README.md) - Automated deployment

## Development

### Setup Development Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
pytest tests/
```

## License

See LICENSE file for details.







