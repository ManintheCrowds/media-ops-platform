# Monitoring Role

This role sets up the monitoring stack including Prometheus, Alertmanager, Grafana, and exporters.

## Variables

- `monitoring_config_path`: Path for monitoring configs (default: /etc/monitoring)
- `monitoring_data_path`: Path for monitoring data (default: /var/lib/monitoring)
- `prometheus_port`: Prometheus port (default: 9090)
- `grafana_port`: Grafana port (default: 3000)
- `alertmanager_port`: Alertmanager port (default: 9093)
- `node_exporter_enabled`: Enable Node Exporter (default: true)
- `cadvisor_enabled`: Enable cAdvisor (default: true)
- `postgres_exporter_enabled`: Enable PostgreSQL Exporter (default: true)
- `alert_email_to`: Email address for alerts
- `smtp_host`: SMTP server hostname
- `smtp_from`: Email sender address

## Features

- Installs and configures Prometheus
- Sets up Alertmanager with email notifications
- Configures Grafana with data sources
- Deploys Node Exporter, cAdvisor, and PostgreSQL Exporter
- Configures alert rules
