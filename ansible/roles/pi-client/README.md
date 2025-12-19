# Pi Client Role

This role provisions and configures Raspberry Pi devices with the pi-client application.

## Variables

- `pi_client_install_path`: Installation path (default: /opt/pi-client)
- `pi_client_config_path`: Configuration path (default: /etc/pi-client)
- `pi_client_data_path`: Data path (default: /var/lib/pi-client)
- `pi_client_version`: Client version to install (default: latest)
- `device_id`: Device identifier (from inventory)
- `device_name`: Device name (from inventory)
- `pi_device_type`: Device type (default: kiosk)
- `pi_organization_id`: Organization ID (default: 1)
- `pi_hardware_enabled`: Enable hardware packages (default: true)
- `pi_generate_certificate`: Generate device certificate (default: true)
- `pi_register_device`: Register device with platform (default: true)
- `pi_registration_token`: Token for device registration
- `pi_api_token`: API token for pi-client

## Features

- Installs pi-client application
- Creates systemd service
- Generates device certificates
- Configures device settings
- Registers device with platform
- Manages configuration updates
