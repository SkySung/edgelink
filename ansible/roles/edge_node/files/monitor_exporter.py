import time
import subprocess
import re
from prometheus_client import start_http_server, Gauge

EXPORTER_PORT = 8000
TARGET_IP = "10.10.10.1"

LATENCY_GAUGE = Gauge('edgelink_ping_latency_ms', 'ICMP Latency to Hub', ['destination'])
LOSS_GAUGE = Gauge('edgelink_packet_loss_percent', 'Packet Loss Percentage', ['destination'])
JITTER_GAUGE = Gauge('edgelink_jitter_ms', 'Network Jitter (mdev)', ['destination'])

def ping_target(ip: str):
    try:
        cmd = ["ping", "-c", "4", "-i", "0.2", "-W", "1", ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        loss_match = re.search(r'(\d+)% packet loss', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        rtt_match = re.search(r'rtt min/avg/max/(?:mdev|stddev) = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+) ms', output)
        
        if rtt_match:
            avg_latency = float(rtt_match.group(2))
            jitter = float(rtt_match.group(4))
        else:
            avg_latency = 0.0
            jitter = 0.0

        return avg_latency, packet_loss, jitter
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return 0.0, 100.0, 0.0

if __name__ == '__main__':
    print(f"Starting Prometheus Exporter on port {EXPORTER_PORT}...")
    start_http_server(EXPORTER_PORT)
    print(f"Start monitoring target: {TARGET_IP}")
    
    while True:
        lat, loss, jit = ping_target(TARGET_IP)
        
        LATENCY_GAUGE.labels(destination=TARGET_IP).set(lat)
        LOSS_GAUGE.labels(destination=TARGET_IP).set(loss)
        JITTER_GAUGE.labels(destination=TARGET_IP).set(jit)
        
        print(f"Updated: Latency={lat}ms, Loss={loss}%, Jitter={jit}ms")
        time.sleep(1)