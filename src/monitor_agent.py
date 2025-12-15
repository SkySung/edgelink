#!/usr/bin/env python3
import subprocess
import time
import sys

# Config
INTERFACE = "wg0"
MAX_UPLOAD_BW_MBPS = 30.0
SATURATION_THRESHOLD = 0.8  # 80% capacity
CHECK_INTERVAL = 60 # seconds

def get_wireguard_stats():
    """
    Parses 'wg show dump' to get active peer count and current throughput.
    Logic: A peer is 'active' if handshake was < 3 mins ago.
    """
    try:
        # wg show dump format: public-key, psk, endpoint, allowed-ips, latest-handshake, transfer-rx, transfer-tx, ...
        # sudo is required for wg commands
        output = subprocess.check_output(
            ["sudo", "wg", "show", INTERFACE, "dump"], 
            universal_newlines=True
        ).strip().splitlines()

        current_time = time.time()
        active_users = 0
        
        for line in output:
            parts = line.split('\t')
            if len(parts) < 5: continue
            
            latest_handshake = int(parts[4])
            if (current_time - latest_handshake) < 180:
                active_users += 1

        # Read kernel stats for throughput (more accurate for real-time load)
        tx_path = f"/sys/class/net/{INTERFACE}/statistics/tx_bytes"
        with open(tx_path, 'r') as f: t1 = int(f.read())
        time.sleep(1)
        with open(tx_path, 'r') as f: t2 = int(f.read())
        
        current_mbps = (t2 - t1) * 8 / 1_000_000
        return active_users, current_mbps

    except Exception as e:
        # Fail safe: assume 0 load if permission denied or interface missing
        print(f"[Error] reading stats: {e}", file=sys.stderr)
        return 0, 0.0

def main():
    print(f"[*] Starting EdgeLink Traffic Governor on {INTERFACE}...")
    
    while True:
        users, mbps = get_wireguard_stats()
        load_ratio = mbps / MAX_UPLOAD_BW_MBPS
        
        status = f"Users: {users} | Load: {mbps:.2f} Mbps ({load_ratio*100:.1f}%)"
        
        # Traffic Governance Logic
        if load_ratio > SATURATION_THRESHOLD:
            print(f"[CRITICAL] {status} -> BACKOFF INITIATED")
            # In a real scenario, we would pause the speedtest cronjob here
            # e.g., subprocess.run(["systemctl", "stop", "speedtest.service"])
        elif users > 2:
            print(f"[WARN] {status} -> QoS Monitoring Active")
        else:
            print(f"[OK] {status}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping agent.")