"""
pfSense Log Parser for Cursor Traffic
Parses pfSense firewall logs and exports metrics for Prometheus
"""

import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class PfSenseLogParser:
    """Parse pfSense firewall logs for Cursor traffic."""
    
    # Common pfSense log patterns
    LOG_PATTERNS = {
        'firewall': re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'
            r'.*?'
            r'rule\s+(\d+).*?'
            r'(\w+)\s+'
            r'(\S+)\s+'
            r'(\S+):(\d+)\s+->\s+'
            r'(\S+):(\d+)'
        ),
        'syslog': re.compile(
            r'<(\d+)>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'
            r'.*?'
            r'(\S+)\s+'
            r'(\S+):(\d+)\s+->\s+'
            r'(\S+):(\d+)'
        )
    }
    
    # Cursor domain patterns
    CURSOR_DOMAINS = [
        'api.cursor.com',
        'cdn.cursor.com',
        '*.cursor.sh'
    ]
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize parser."""
        self.log_file = log_file
        self.metrics = {
            'connections_total': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections_by_endpoint': {},
            'connections_by_port': {},
            'errors': 0
        }
        self.last_position = 0
        
    def is_cursor_traffic(self, destination: str) -> bool:
        """Check if destination is a Cursor endpoint."""
        for domain in self.CURSOR_DOMAINS:
            if domain.startswith('*'):
                pattern = domain.replace('*', '.*')
                if re.match(pattern, destination):
                    return True
            elif domain in destination:
                return True
        return destination in self.metrics.get('known_ips', [])
    
    def parse_firewall_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single firewall log line."""
        match = self.LOG_PATTERNS['firewall'].search(line)
        if not match:
            return None
        
        timestamp, rule_id, action, src_ip, src_port, dst_ip, dst_port = match.groups()
        
        # Check if this is Cursor traffic
        if not self.is_cursor_traffic(dst_ip):
            return None
        
        return {
            'timestamp': timestamp,
            'rule_id': rule_id,
            'action': action,
            'source': {
                'ip': src_ip,
                'port': int(src_port)
            },
            'destination': {
                'ip': dst_ip,
                'port': int(dst_port)
            }
        }
    
    def parse_syslog_line(self, line: str) -> Optional[Dict]:
        """Parse a single syslog line."""
        match = self.LOG_PATTERNS['syslog'].search(line)
        if not match:
            return None
        
        priority, timestamp, src_ip, src_port, dst_ip, dst_port = match.groups()
        
        # Check if this is Cursor traffic
        if not self.is_cursor_traffic(dst_ip):
            return None
        
        return {
            'timestamp': timestamp,
            'priority': int(priority),
            'source': {
                'ip': src_ip,
                'port': int(src_port)
            },
            'destination': {
                'ip': dst_ip,
                'port': int(dst_port)
            }
        }
    
    def parse_log_file(self, log_file: Optional[str] = None) -> List[Dict]:
        """Parse log file and return events."""
        log_path = log_file or self.log_file
        if not log_path or not Path(log_path).exists():
            return []
        
        events = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last position for incremental reading
                f.seek(self.last_position)
                
                for line in f:
                    # Try firewall log format first
                    event = self.parse_firewall_log_line(line)
                    if not event:
                        # Try syslog format
                        event = self.parse_syslog_line(line)
                    
                    if event:
                        events.append(event)
                
                self.last_position = f.tell()
        except Exception as e:
            print(f"Error parsing log file: {e}")
        
        return events
    
    def update_metrics(self, events: List[Dict]):
        """Update metrics from parsed events."""
        for event in events:
            self.metrics['connections_total'] += 1
            
            dst = event.get('destination', {})
            endpoint = dst.get('ip', 'unknown')
            port = dst.get('port', 0)
            
            # Update endpoint metrics
            if endpoint not in self.metrics['connections_by_endpoint']:
                self.metrics['connections_by_endpoint'][endpoint] = 0
            self.metrics['connections_by_endpoint'][endpoint] += 1
            
            # Update port metrics
            if port not in self.metrics['connections_by_port']:
                self.metrics['connections_by_port'][port] = 0
            self.metrics['connections_by_port'][port] += 1
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Connection count
        lines.append(f"cursor_pfsense_connections_total {self.metrics['connections_total']}")
        
        # Connections by endpoint
        for endpoint, count in self.metrics['connections_by_endpoint'].items():
            lines.append(f'cursor_pfsense_connections_by_endpoint{{endpoint="{endpoint}"}} {count}')
        
        # Connections by port
        for port, count in self.metrics['connections_by_port'].items():
            lines.append(f'cursor_pfsense_connections_by_port{{port="{port}"}} {count}')
        
        # Error count
        lines.append(f"cursor_pfsense_errors_total {self.metrics['errors']}")
        
        return '\n'.join(lines)
    
    def export_json_metrics(self) -> str:
        """Export metrics in JSON format."""
        return json.dumps(self.metrics, indent=2)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse pfSense logs for Cursor traffic')
    parser.add_argument('--log-file', help='Path to log file')
    parser.add_argument('--output', choices=['prometheus', 'json'], default='prometheus',
                       help='Output format')
    parser.add_argument('--output-file', help='Output file path')
    
    args = parser.parse_args()
    
    parser = PfSenseLogParser(log_file=args.log_file)
    events = parser.parse_log_file()
    parser.update_metrics(events)
    
    if args.output == 'prometheus':
        output = parser.export_prometheus_metrics()
    else:
        output = parser.export_json_metrics()
    
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(output)
    else:
        print(output)


if __name__ == '__main__':
    main()
