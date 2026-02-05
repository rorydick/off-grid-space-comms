## Mesh Networking Principles

Mesh networking is a communication architecture where devices (nodes) connect directly to each other and cooperatively route data. Instead of relying on a central hub or infrastructure, each node acts as a router, forwarding data to its neighbors. This decentralized approach offers several advantages:

- **Resilience:** If one node fails, the network can continue to operate by routing data through other paths.
- **Scalability:** Adding more nodes increases the network's coverage and capacity.
- **Flexibility:** Mesh networks can be deployed in diverse environments without the need for pre-existing infrastructure.

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed technical comparison of protocols and power profiles.

## Simulation Prototype

A lightweight, dependency-free simulator is available in [`sim/`](sim/) to explore how node density and simple terrain attenuation impact mesh connectivity.

- Entry point: `python3 sim/mesh_sim.py --help`
- Docs: [`sim/README.md`](sim/README.md)

## Comparative Technology Overview

| Technology | PHY / Protocol | Use Case | Strengths |
| :--- | :--- | :--- | :--- |
| **Meshtastic** | LoRa / Custom Mesh | Off-grid messaging, outdoors | User-friendly, massive community, broad hardware support. |
| **Reticulum** | Agnostic (LoRa, WiFi, HF) | Unstoppable, private networks | Crypto-native, extremely resilient, medium-agnostic. |
| **MeshCore** | LoRa / Hybrid Routing | Custom embedded solutions | Lightweight, balanced between Meshtastic and Reticulum. |
| **LunaNet** | DTN / BP / 802.11 | Lunar/Martian surface infrastructure | Interoperable standards, space-grade, supports high latency. |

## Use Cases for Lunar/Martian Habitats

1. **EVA Emergency Backup:** Primary comms (LTE/WiFi) rely on base stations. A LoRa-based mesh provides a low-power "pager" system for life-critical alerts if primary infrastructure fails.
2. **Distributed Sensor Arrays:** Deploying hundreds of environmental sensors across varied terrain without cabling or power-hungry high-bandwidth radios.
3. **Local Navigation Beacons:** Mesh nodes can serve as static anchors for relative positioning where GPS is unavailable.
4. **Disaster Recovery:** In the event of habitat depressurization or module loss, autonomous mesh nodes can facilitate coordination between isolated groups.