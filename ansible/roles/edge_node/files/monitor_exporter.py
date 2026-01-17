import time
import subprocess
import re
from prometheus_client import start_http_server, Gauge

# Port exposed for Prometheus scraping
EXPORTER_PORT = 8000
# Target IP to ping (GCP Hub via WireGuard tunnel)
TARGET_IP = "10.10.10.1"

# Metrics
LATENCY_GAUGE = Gauge('edgelink_ping_latency_ms', 'ICMP Latency to Hub', ['destination'])
LOSS_GAUGE = Gauge('edgelink_packet_loss_percent', 'Packet Loss Percentage', ['destination'])
JITTER_GAUGE = Gauge('edgelink_jitter_ms', 'Network Jitter (mdev)', ['destination'])


def ping_target(ip: str):
    """
    Executes the system ping command and parses the output.
    Returns: (latency_ms, packet_loss_percent, jitter_ms)
    """
    try:
        # Send 4 ICMP packets at 0.2s interval, 1s timeout per packet
        cmd = ["ping", "-c", "4", "-i", "0.2", "-W", "1", ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        # Packet loss
        loss_match = re.search(r'(\\d+)% packet loss', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # RTT stats (Linux: mdev; some systems: stddev)
        rtt_match = re.search(r'rtt min/avg/max/(?:mdev|stddev) = ([\\d\\.]+)/([\\d\\.]+)/([\\d\\.]+)/([\\d\\.]+) ms', output)
        if rtt_match:
            avg_latency = float(rtt_match.group(2))
            jitter = float(rtt_match.group(4))
        else:
            avg_latency = 0.0
            jitter = 0.0

        return avg_latency, packet_loss, jitter
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        # Treat execution error as 100% packet loss
        return 0.0, 100.0, 0.0


if __name__ == '__main__':
    # Start HTTP server for Prometheus to scrape
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

