# Project To-Do List

This document outlines current and upcoming tasks for the 'Off-Grid Communications for Space Settlements and Disaster Contingency' project. Contributions are welcome!

## Immediate Tasks:

- [x] Research existing off-grid communication technologies beyond Meshtastic (e.g., LoRa, amateur radio, satellite phones).
- [x] Draft an initial section on the principles of mesh networking for the `README.md`.
- [x] Outline potential use cases for off-grid comms in lunar/Martian habitats.
- [x] Investigate power consumption profiles of common Meshtastic devices.
- [x] Draft a "Technical Architecture" section comparing DTN (Delay Tolerant Networking) with mesh protocols.

## Future Tasks:

- [x] Develop a simple simulation model for mesh network propagation in varied terrain. (See `sim/mesh_sim.py`.)
- [x] Design a preliminary concept for a space-hardened Meshtastic node. (See `SPACE_HARDENED_NODE.md`.)
- [x] Explore methods for integrating off-grid comms with emergency services on Earth. (See `EMERGENCY_INTEGRATION.md`.)
- [x] Begin drafting a section on regulatory considerations for space-based off-grid comms. (See `REGULATORY.md`.)
- [x] Implement multi-hop 'relay' metrics in the simulator to better model path congestion.
- [ ] Implement a simple 'power-budget' mode in the simulator to track total energy cost of a message broadcast.
- [ ] Research and add technical specs for 'Interplanetary Overlay' protocol.
