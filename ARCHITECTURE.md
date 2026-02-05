## Technical Architecture: DTN vs. Mesh

In the context of space and off-grid communications, two primary architectural patterns emerge: traditional Mesh Networking (like Meshtastic) and Delay/Disruption Tolerant Networking (DTN).

### 1. Mesh Networking (e.g., Meshtastic)
*   **Protocol:** Custom flooding/routing protocols over LoRa.
*   **Connectivity:** Requires a near-continuous end-to-end path (even if multi-hop) for reliable delivery.
*   **Latency:** Low (seconds) when a path exists.
*   **Use Case:** Real-time tactical communication within a settlement or localized mission.

### 2. Delay/Disruption Tolerant Networking (DTN)
*   **Protocol:** Bundle Protocol (BP), often used with Licklider Transmission Protocol (LTP).
*   **Mechanism:** "Store-Carry-Forward." Nodes store data bundles until a connection to the next hop becomes available.
*   **Connectivity:** Designed for intermittently connected networks where an end-to-end path may never exist at a single point in time.
*   **Latency:** High (minutes to hours).
*   **Use Case:** Inter-settlement communication, orbit-to-surface links, and long-range exploration.

### Comparison Table

| Feature | Mesh (Meshtastic) | DTN (NASA ION/BP) |
| :--- | :--- | :--- |
| **Primary Goal** | Real-time connectivity | Reliable delivery over time |
| **Node Storage** | Minimal (volatile buffer) | Significant (persistent storage) |
| **Pathfinding** | Reactive/Flooding | Scheduled/Opportunistic |
| **Complexity** | Low (Plug & Play) | High (Requires contact graph) |

## Power Consumption Profiles

For space missions, energy is the most constrained resource. Modern off-grid devices vary significantly in power efficiency based on their chipset.

| Chipset Family | Standby Current | Peak TX Current | Estimated Life (1000mAh) |
| :--- | :--- | :--- | :--- |
| **ESP32 (e.g., Heltec V3)** | ~50-80 mA | ~120-150 mA | ~12-18 hours |
| **nRF52 (e.g., RAK4631)** | ~2-5 mA | ~10-25 mA | ~5-10 days |
| **RP2040 (e.g., Pico)** | ~20-30 mA | ~90-110 mA | ~1-2 days |

*Data based on standard Meshtastic firmware configurations.*

**Recommendation for Lunar/Martian Deployments:** nRF52-based architectures are mandatory for autonomous nodes (beacons/sensors) to minimize solar array size and battery mass. ESP32 is suitable only for base-powered hub stations.
