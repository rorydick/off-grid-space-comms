# Interplanetary Overlay Network (ION) & DTN Specs

The Interplanetary Overlay Network (ION) is an implementation of the Delay-Tolerant Networking (DTN) architecture, specifically designed for use in space environments where traditional TCP/IP fails due to high latency, frequent disruptions, and low link quality.

## Core Protocols

| Protocol | Name | Function | Space Standard |
| :--- | :--- | :--- | :--- |
| **BP** | Bundle Protocol | The "IP of space". Encapsulates data into bundles with hop-by-hop persistence. | RFC 5050 / CCSDS 734.2-B-1 |
| **LTP** | Licklider Transmission Protocol | Reliable data transport over deep-space links using retransmission (ARQ). | RFC 5326 / CCSDS 734.1-B-1 |
| **CFDP** | CCSDS File Delivery Protocol | Managed file transfer across heterogeneous space/ground networks. | CCSDS 727.0-B-5 |
| **BSS** | Bundle Streaming Service | Optimized delivery for time-sensitive data (telemetry/video). | - |

## Key Technical Specifications

### 1. Persistence & Convergence
Unlike terrestrial routers that discard packets if a link is down, DTN nodes (ION) store bundles in persistent storage (non-volatile memory) until a next-hop contact is available.

### 2. Convergence Layers (CL)
ION allows BP to run over various underlying protocols via Convergence Layers:
- **TCPCL:** For stable ground/habitat links.
- **UDPCL:** For low-overhead local mesh links.
- **LTPCL:** For high-latency, asymmetric space links (e.g., Earth-Mars).

### 3. Contact Graph Routing (CGR)
Instead of dynamic discovery (like OSPF/BGP), CGR uses a pre-calculated "Contact Graph" (ephemeris-based schedule of when nodes can see each other) to determine the best path through a moving constellation.

## Application in Off-Grid Mesh
In a lunar/Martian habitat mesh, ION/BP provides:
- **Asynchrony:** A sensor can send a message even if the base station is currently over the horizon.
- **Interoperability:** The local LoRa mesh can pass bundles to an orbiting satellite which then relays them to Earth using a different physical layer.
- **Reliability:** Data is not lost during signal "shadows" caused by terrain or orbital mechanics.

## Implementation Reference
- **ION (Interplanetary Overlay Network):** NASA/JPL's open-source implementation (C).
- **µD3TN:** Lightweight DTN implementation for embedded/small-sat use.
- **PyDTN:** Python-based implementation for simulation and prototyping.
