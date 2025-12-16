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
echo "[-] Pulling Tetragon Docker image (v1.1.2 from Quay.io)..."
# 定義目標 Image，包含版本號 (Pin Version)
TARGET_IMAGE="quay.io/cilium/tetragon:v1.1.2"
LOCAL_TAG="cilium/tetragon:latest"

# 拉取正確的 Image
if ! docker images | grep -q "$TARGET_IMAGE"; then
    sudo docker pull $TARGET_IMAGE
    # 自動幫你打上 Tag，讓舊的 Tool 也能相容
    sudo docker tag $TARGET_IMAGE $LOCAL_TAG
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