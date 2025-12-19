"""
Cursor Prometheus Exporter
Exports Cursor connection metrics in Prometheus format
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST


# Prometheus metrics
cursor_connections_active = Gauge(
    'cursor_connections_active',
    'Current number of active Cursor connections',
    ['endpoint']
)

cursor_connections_total = Counter(
    'cursor_connections_total',
    'Total number of Cursor connection attempts',
    ['endpoint', 'state']
)

cursor_connection_duration_seconds = Histogram(
    'cursor_connection_duration_seconds',
    'Connection duration in seconds',
    ['endpoint'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

cursor_bytes_sent_total = Counter(
    'cursor_bytes_sent_total',
    'Total bytes sent to Cursor endpoints',
    ['endpoint']
)

cursor_bytes_received_total = Counter(
    'cursor_bytes_received_total',
    'Total bytes received from Cursor endpoints',
    ['endpoint']
)

cursor_latency_seconds = Gauge(
    'cursor_latency_seconds',
    'Latency to Cursor endpoints in seconds',
    ['endpoint']
)

cursor_packet_loss_ratio = Gauge(
    'cursor_packet_loss_ratio',
    'Packet loss ratio to Cursor endpoints',
    ['endpoint']
)

cursor_dns_resolution_seconds = Gauge(
    'cursor_dns_resolution_seconds',
    'DNS resolution time in seconds',
    ['endpoint']
)

cursor_connection_errors_total = Counter(
    'cursor_connection_errors_total',
    'Total connection errors',
    ['endpoint', 'error_type']
)

cursor_disconnects_total = Counter(
    'cursor_disconnects_total',
    'Total disconnect events',
    ['endpoint', 'reason']
)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'healthy'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class CursorExporter:
    """Main exporter class."""
    
    def __init__(
        self,
        metrics_dir: str = 'cursor-metrics',
        quality_dir: str = 'cursor-quality-metrics',
        event_log_dir: str = 'cursor-event-logs'
    ):
        """Initialize exporter."""
        self.metrics_dir = Path(metrics_dir)
        self.quality_dir = Path(quality_dir)
        self.event_log_dir = Path(event_log_dir)
        self.last_processed = {}
    
    def load_connection_metrics(self) -> List[Dict]:
        """Load connection metrics from JSON files."""
        metrics = []
        
        if not self.metrics_dir.exists():
            return metrics
        
        for json_file in self.metrics_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'Metrics' in data:
                        metrics.append(data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return metrics
    
    def load_quality_metrics(self) -> List[Dict]:
        """Load quality metrics from JSON files."""
        metrics = []
        
        if not self.quality_dir.exists():
            return metrics
        
        for json_file in self.quality_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'Endpoints' in data:
                        metrics.append(data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return metrics
    
    def update_connection_metrics(self, metrics: List[Dict]):
        """Update Prometheus metrics from connection data."""
        for metric_data in metrics:
            if 'Metrics' not in metric_data:
                continue
            
            metrics_obj = metric_data['Metrics']
            timestamp = metric_data.get('Timestamp', '')
            
            # Active connections
            active = metrics_obj.get('ActiveConnections', 0)
            cursor_connections_active.labels(endpoint='all').set(active)
            
            # Total connections
            total = metrics_obj.get('TotalConnections', 0)
            cursor_connections_total.labels(endpoint='all', state='total').inc(total)
            
            # Connections by state
            states = metrics_obj.get('ConnectionsByState', {})
            for state, count in states.items():
                cursor_connections_total.labels(endpoint='all', state=state.lower()).inc(count)
            
            # Bytes sent/received (if available)
            bytes_sent = metrics_obj.get('BytesSent', 0)
            bytes_received = metrics_obj.get('BytesReceived', 0)
            if bytes_sent > 0:
                cursor_bytes_sent_total.labels(endpoint='all').inc(bytes_sent)
            if bytes_received > 0:
                cursor_bytes_received_total.labels(endpoint='all').inc(bytes_received)
    
    def update_quality_metrics(self, metrics: List[Dict]):
        """Update Prometheus metrics from quality data."""
        for metric_data in metrics:
            if 'Endpoints' not in metric_data:
                continue
            
            endpoints = metric_data['Endpoints']
            
            for endpoint_name, endpoint_data in endpoints.items():
                # DNS metrics
                dns_results = endpoint_data.get('DNSResults', [])
                if dns_results:
                    latest_dns = dns_results[-1]
                    if latest_dns.get('Resolved') and latest_dns.get('ResolutionTime'):
                        resolution_time = latest_dns['ResolutionTime'] / 1000.0  # Convert to seconds
                        cursor_dns_resolution_seconds.labels(endpoint=endpoint_name).set(resolution_time)
                
                # Ping metrics
                ping_results = endpoint_data.get('PingResults', [])
                if ping_results:
                    latest_ping = ping_results[-1]
                    if latest_ping.get('Success'):
                        latency = latest_ping.get('LatencyAvg', 0) / 1000.0  # Convert to seconds
                        packet_loss = latest_ping.get('PacketLossPercent', 0) / 100.0  # Convert to ratio
                        cursor_latency_seconds.labels(endpoint=endpoint_name).set(latency)
                        cursor_packet_loss_ratio.labels(endpoint=endpoint_name).set(packet_loss)
                
                # HTTP metrics
                http_results = endpoint_data.get('HTTPResults', [])
                if http_results:
                    latest_http = http_results[-1]
                    if latest_http.get('Success') and latest_http.get('Latency'):
                        http_latency = latest_http['Latency'] / 1000.0  # Convert to seconds
                        # Use HTTP latency as connection latency if ping not available
                        if not ping_results:
                            cursor_latency_seconds.labels(endpoint=endpoint_name).set(http_latency)
    
    def collect_metrics(self):
        """Collect and update all metrics."""
        # Load and update connection metrics
        connection_metrics = self.load_connection_metrics()
        self.update_connection_metrics(connection_metrics)
        
        # Load and update quality metrics
        quality_metrics = self.load_quality_metrics()
        self.update_quality_metrics(quality_metrics)
    
    def run(self, port: int = 9101, interval: int = 30):
        """Run the exporter server."""
        def collect_periodically():
            while True:
                self.collect_metrics()
                time.sleep(interval)
        
        import threading
        collector_thread = threading.Thread(target=collect_periodically, daemon=True)
        collector_thread.start()
        
        server = HTTPServer(('0.0.0.0', port), MetricsHandler)
        print(f"Cursor exporter running on port {port}")
        print(f"Metrics endpoint: http://localhost:{port}/metrics")
        print(f"Health endpoint: http://localhost:{port}/health")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down exporter...")
            server.shutdown()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cursor Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9101, help='Exporter port')
    parser.add_argument('--interval', type=int, default=30, help='Collection interval in seconds')
    parser.add_argument('--metrics-dir', default='cursor-metrics', help='Metrics directory')
    parser.add_argument('--quality-dir', default='cursor-quality-metrics', help='Quality metrics directory')
    parser.add_argument('--event-log-dir', default='cursor-event-logs', help='Event log directory')
    
    args = parser.parse_args()
    
    exporter = CursorExporter(
        metrics_dir=args.metrics_dir,
        quality_dir=args.quality_dir,
        event_log_dir=args.event_log_dir
    )
    
    exporter.run(port=args.port, interval=args.interval)


if __name__ == '__main__':
    main()
