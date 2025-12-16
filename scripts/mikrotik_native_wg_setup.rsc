# ==========================================
# EdgeLink Project: Native WireGuard Setup
# Author: Sky Sung
# Target: MikroTik E50UG (RouterOS v7)
# Description: Sets up WG Server without Containers/USB
# ==========================================

# === CONFIGURATION ===
# 定義你的 WireGuard 介面名稱
:local wgName "edge-wg0"
# 定義 VPN 內網 IP (Gateway)
:local wgAddress "10.10.10.1/24"
# 定義監聽 Port (標準是 51820)
:local listenPort 51820

# === 1. 建立 WireGuard 介面 ===
:put "[*] Creating WireGuard Interface..."
if ([:len [/interface/wireguard/find name=$wgName]] = 0) do={
    /interface/wireguard/add name=$wgName listen-port=$listenPort comment="EdgeLink-VPN-Gateway"
} else={
    :put "    Interface $wgName already exists."
}

# === 2. 分配 IP 位址 ===
:put "[*] Assigning IP Address..."
if ([:len [/ip/address/find interface=$wgName]] = 0) do={
    /ip/address/add address=$wgAddress interface=$wgName network=10.10.10.0
}

# === 3. 設定防火牆 (關鍵！否則連不進來) ===
:put "[*] Configuring Firewall (Allow UDP $listenPort)..."
# 確保 Input Chain 允許 UDP 51820
if ([:len [/ip/firewall/filter/find dst-port=$listenPort protocol=udp chain=input]] = 0) do={
    # 注意：這裡將規則加在最上面 (place-before=0)，確保不被 Drop 規則擋住
    /ip/firewall/filter/add chain=input protocol=udp dst-port=$listenPort action=accept comment="Allow-WireGuard-Handshake" place-before=0
}

# === 4. 啟用 Cloud DDNS (解決浮動 IP 問題) ===
:put "[*] Enabling MikroTik Cloud DDNS..."
/ip/cloud/set ddns-enabled=yes

# === 5. 輸出連線資訊 ===
:delay 2s
:local pubKey [/interface/wireguard/get [find name=$wgName] public-key]
:local dnsName [/ip/cloud/get dns-name]

:put "=================================================="
:put " [SETUP COMPLETE] Setup Info for Client (Pi):"
:put "=================================================="
:put " Endpoint Host: $dnsName"
:put " Endpoint Port: $listenPort"
:put " Server Public Key: $pubKey"
:put " Server VPN IP: 10.10.10.1"
:put "=================================================="
:put "NEXT STEP: Copy 'Server Public Key' and 'Endpoint Host' to your Pi's wg0.conf"