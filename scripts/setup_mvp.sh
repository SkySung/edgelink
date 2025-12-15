#!/bin/bash
# EdgeLink Node Setup Script (MVP Version)
# Author: Sky Sung
# TODO: Refactor this entire script into Ansible Playbook for idempotency (ETA: Next Sprint)

set -e # Exit on error

echo "[*] Initializing EdgeLink Node Setup..."

# 1. Update System
echo "[-] Updating apt repositories..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Dependencies (Docker, WireGuard, Python3)
echo "[-] Installing core packages..."
sudo apt-get install -y wireguard docker.io python3-pip jq curl

# 3. Setup Tetragon (eBPF Observability)
# Note: Requires kernel headers
echo "[-] Pulling Tetragon Docker image..."
if ! docker images | grep -q "cilium/tetragon"; then
    sudo docker pull cilium/tetragon:latest
else
    echo "    Tetragon image already exists."
fi

# 4. Install Speedtest CLI (Official Ookla)
if [ ! -f /usr/bin/speedtest ]; then
    echo "[-] Installing Ookla Speedtest..."
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
    sudo apt-get install speedtest
fi

# 5. Setup Python Agent
echo "[-] Setting up Python environment..."
# pip install -r requirements.txt (skipped for MVP)

echo "[SUCCESS] Node provisioning complete."
echo "NEXT STEP: Configure /etc/wireguard/wg0.conf manually (or wait for Ansible role)."