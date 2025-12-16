# ==========================================
# EdgeLink Project: MikroTik Tailscale Setup
# Author: Sky Sung
# Target: MikroTik E50UG (ARM64)
# Note: Requires 'container' package installed
# ==========================================

# === CONFIGURATION ===
# [SECURITY WARNING] Do NOT commit your actual key to GitHub!
# Replace the string below with your real Tailscale Auth Key before running.
:local tsKey "tskey-auth-REPLACE_WITH_YOUR_KEY_HERE"

# Storage Configuration
# SRE Best Practice: Use external USB ("usb1") to protect internal NAND flash.
# If no USB is present, ensure your internal flash has >100MB free space.
# Check your disk name using: /disk print
:local diskName "usb1" 

# Network Configuration
:local vethName "veth-tailscale"
:local vethAddr "172.17.0.2/24"
:local vethGate "172.17.0.1"
:local bridgeName "docker-bridge"

# === 1. Network Infrastructure (VETH & Bridge) ===
/interface/print count-only
:put "[*] Setting up Network Interfaces..."

# Create VETH interface if not exists
if ([:len [/interface/veth/find name=$vethName]] = 0) do={
    /interface/veth/add name=$vethName address=$vethAddr gateway=$vethGate
}

# Create Bridge if not exists
if ([:len [/interface/bridge/find name=$bridgeName]] = 0) do={
    /interface/bridge/add name=$bridgeName
    /ip/address/add address=($vethGate . "/24") interface=$bridgeName
}

# Add Port to Bridge
if ([:len [/interface/bridge/port/find bridge=$bridgeName interface=$vethName]] = 0) do={
    /interface/bridge/port/add bridge=$bridgeName interface=$vethName
}

# === 2. NAT Masquerade (Outbound Internet Access) ===
:put "[*] Configuring NAT..."
if ([:len [/ip/firewall/nat/find comment="docker-nat"]] = 0) do={
    /ip/firewall/nat/add chain=srcnat action=masquerade src-address=172.17.0.0/24 comment="docker-nat"
}

# === 3. Container Registry & Environment ===
:put "[*] Configuring Container Environment..."
# Set registry and temp directory (Watch out for disk space here!)
/container/config/set registry-url=https://registry-1.docker.io tmpdir=($diskName . "/pull")

# Setup Env Vars
/container/envs/remove [find name="ts_env"]
/container/envs/add name=ts_env key=TS_AUTH_KEY value=$tsKey
/container/envs/add name=ts_env key=TS_HOSTNAME value="MikroTik-HQ"
/container/envs/add name=ts_env key=TS_STATE_DIR value="/var/lib/tailscale"
/container/envs/add name=ts_env key=TS_USERSPACE value="true"
/container/envs/add name=ts_env key=TS_ROUTES value="192.168.88.0/24" 
# ↑ TS_ROUTES is optional: enables Subnet Router mode to access LAN devices

# === 4. Pull & Deploy Container ===
:put "[*] Pulling Tailscale Image (This may take a while)..."
# Note: Ensure you have internet access before running this
/container/add remote-image=tailscale/tailscale:latest \
    interface=$vethName \
    root-dir=($diskName . "/tailscale") \
    envlist=ts_env \
    logging=yes \
    start-on-boot=yes \
    comment="EdgeLink-Tailscale"

# === 5. Start Container ===
:put "[*] Starting Container..."
:delay 5s
/container/start [find comment="EdgeLink-Tailscale"]

:put "[SUCCESS] Tailscale setup script completed."