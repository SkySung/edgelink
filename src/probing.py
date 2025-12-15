#!/usr/bin/env python3
"""
EdgeLink Network Probing Agent
Author: Sky Sung
Description: Latency-aware network health check and traffic governance.
"""

import subprocess
import time
import sys
import os

# Configuration
ISP_GATEWAY = "8.8.8.8"      # Google DNS as reliable target
NEIGHBOR_GATEWAY = "192.168.1.1" # Local Gateway
THRESHOLD_ISP_LATENCY = 100  # ms
THRESHOLD_PACKET_LOSS = 5    # %

def ping_target(host, count=3):
    """
    Pings a target and returns average latency (ms).
    Returns None if unreachable.
    """
    try:
        # -c: count, -W: timeout (seconds)
        output = subprocess.check_output(
            ["ping", "-c", str(count), "-W", "2", host],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Parse output for "min/avg/max"
        # Example line: rtt min/avg/max/mdev = 12.345/15.678/18.901/2.345 ms
        for line in output.splitlines():
            if "rtt min/avg/max" in line or "round-trip min/avg/max" in line:
                avg_latency = float(line.split("=")[1].split("/")[1])
                return avg_latency
                
    except subprocess.CalledProcessError:
        return None
    except Exception as e:
        print(f"[ERROR] Ping failed: {e}", file=sys.stderr)
        return None

def sre_diagnosis():
    """
    Performs a layered diagnosis of network health.
    Layer 1: Local Gateway (Neighbor check)
    Layer 2: ISP Uplink (Congestion check)
    """
    print(f"[*] Starting diagnosis at {time.ctime()}...")

    # Layer 1: Local Gateway Check
    lat_local = ping_target(NEIGHBOR_GATEWAY)
    if lat_local is None:
        print("❌ [CRITICAL] Local Gateway unreachable! Check physical layer/Wi-Fi.", file=sys.stderr)
        return False
    
    if lat_local > 50:
         print(f"⚠️ [WARN] High Local Latency: {lat_local:.2f}ms. Noisy neighbor detected.")
         # Decision: Continue but mark as degraded
    
    # Layer 2: ISP Uplink Check
    lat_isp = ping_target(ISP_GATEWAY)
    if lat_isp is None:
        print("❌ [CRITICAL] ISP Uplink Down! No internet access.", file=sys.stderr)
        return False

    print(f"☁️ ISP Latency: {lat_isp:.2f} ms")

    # SRE Decision Logic
    if lat_isp > THRESHOLD_ISP_LATENCY:
        print(f"⛔ [WARN] ISP Congestion Detected (>{THRESHOLD_ISP_LATENCY}ms).")
        print("   -> Inference: Local loop is fine, but ISP is saturated.")
        print("   -> Decision: BACKOFF initiated. Pausing bandwidth-intensive tasks.")
        return False

    # All Green
    print("✅ [PASS] Network Path Healthy. Ready for traffic.")
    return True

if __name__ == "__main__":
    is_healthy = sre_diagnosis()
    
    if is_healthy:
        print("🚀 Status Green: Starting Speedtest / Upload Task...")
        # In a real scenario, we might trigger another script here
        # os.system("./run_speedtest.sh")
    else:
        print("💤 Status Red/Yellow: Entering Standby Mode (Backoff 5 min).")
        sys.exit(1) # Exit with error code for cron handling