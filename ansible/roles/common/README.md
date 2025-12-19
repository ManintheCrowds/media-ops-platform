# Common Role

This role sets up common server configuration including:
- System updates
- User creation and SSH key setup
- Firewall configuration
- Time synchronization (NTP)
- Log rotation

## Variables

- `system_users`: List of system users to create
- `timezone`: System timezone (default: UTC)
- `ntp_servers`: List of NTP servers
- `firewall_enabled`: Enable firewall (default: true)
- `firewall_allowed_tcp_ports`: List of allowed TCP ports
- `logrotate_enabled`: Enable log rotation (default: true)
- `logrotate_retention_days`: Days to retain logs (default: 30)
