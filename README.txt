Project EdgeLink-SRE

Hybrid Cloud Network Observability & Traffic Governance Lab

Overview

EdgeLink is a research project designed to simulate enterprise edge connectivity issues.
It focuses on two main challenges:

Visibility: Using eBPF (Tetragon) to trace network events at the kernel level, attributing latency spikes to specific processes.

Reliability: Solving Carrier-Grade NAT (CGNAT) traversal using WireGuard with a custom Python Telemetry Agent for latency-aware traffic governance.

Architecture

graph TD
    subgraph HQ [Site A: Home/HQ]
        Router[MikroTik hEX] 
        Validation[Validation Client]
    end

    subgraph Branch [Site B: Edge Node]
        Pi[Raspberry Pi 4]
        Agent[Python Governance Agent]
        Tetragon[eBPF Tetragon Probe]
        WG_Client[WireGuard Interface]
    end

    Internet((Internet / CGNAT))

    %% Connections
    Router <==>|"VPN Tunnel (UDP 51820)"| Internet
    Internet <==>|"Keep-Alive: 25s"| WG_Client
    
    %% Internal Logic
    WG_Client --> Agent
    Tetragon -.->|"Kernel Trace"| Agent
    Agent -->|"Backoff Signal"| WG_Client


Key Features

Smart Traffic Governance:

Monitors WireGuard interface throughput and active peer count in real-time.

Implements a Backoff Algorithm: automatically pauses background bandwidth testing (Speedtest) when user traffic saturation > 80%.

Solves the "Noisy Neighbor" problem in multi-tenant edge environments.

Kernel-Level Observability:

Leverages Cilium Tetragon to bypass standard iptables logs.

Traces tcp_connect and kfree_skb syscalls to identify dropped packets and connection attempts at the process level.

Resilient Connectivity:

Uses WireGuard Persistent Keep-alives to punch through ISP NAT.

Configured for Split Tunneling (optimizing Netflix/Youtube traffic routing).

Quick Start (MVP)

Note: The environment is currently transitioning from Shell Scripts to Ansible for better reproducibility.

1. Provisioning (Legacy Shell)

sudo ./scripts/setup_mvp.sh


2. Run Governance Agent

sudo python3 src/monitor_agent.py


Roadmap

[x] Phase 1: Connectivity (WireGuard Site-to-Site)

[x] Phase 2: Observability (Python Agent + Basic eBPF)

[ ] Phase 3: Refactoring to Ansible Playbooks (In Progress)

Goal: Replace setup_mvp.sh with idempotent roles.

[ ] Phase 4: Integration with Prometheus/Grafana Dashboard.