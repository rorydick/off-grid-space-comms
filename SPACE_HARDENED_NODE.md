# Preliminary Concept: Space‑Hardened Meshtastic Node

This document sketches a **first-pass** concept for adapting a Meshtastic-class LoRa mesh node to harsh environments (lunar/Martian surface, or Earth disaster response with extreme temperatures and dust).

It is **not** a detailed hardware design. The goal is to identify the major engineering drivers and propose a plausible architecture that can be refined later.

## 1) Mission framing (what “space-hardened” means here)

There are two very different target regimes:

1. **Terrestrial disaster / expedition hardware**
   - Wide temperature swings, rain/dust, vibration, long storage, poor charging.
   - *No radiation hardening requirement* beyond normal electronics robustness.

2. **Planetary surface outpost (Moon/Mars)**
   - Vacuum (Moon), CO₂ thin atmosphere (Mars), dust, thermal extremes.
   - Radiation environment (TID + SEEs), long unattended ops.
   - In many cases the practical approach is **shielded COTS** with derating and redundancy, not “true rad-hard” parts.

This concept assumes **shielded COTS + careful packaging**, because true rad-hard parts and qualified manufacturing push cost/complexity very high.

## 2) Functional requirements (proposed)

- **Primary function:** low-rate emergency messaging + telemetry relay.
- **Range driver:** link budget, antenna placement, and terrain; expect multi-hop.
- **Power:** weeks/months of unattended operation; aggressive sleep.
- **Reliability:** tolerate intermittent node failures and still provide network coverage.
- **Interfaces:** simple field service (swap battery, attach antenna, read status).

## 3) High-level architecture

### 3.1 Compute / control

- MCU-based design (low power, deterministic):
  - **STM32L4/L5**-class or **nRF52**-class MCU (Meshtastic commonly uses ESP32 in some hardware, but ESP32 power and SEU tolerance may be less attractive for long unattended duty cycles).
- External watchdog + brownout handling.
- FRAM or robust flash strategy for logs and key material.

### 3.2 Radio subsystem

- Semtech LoRa transceiver family:
  - SX1262 / SX1276‑class.
- PA/LNA optional depending on desired EIRP and receive margin.
- **SAW / bandpass filtering** and ESD protection on RF line.
- Frequency options (mission dependent): 433/868/915 MHz on Earth; a dedicated band for extra-terrestrial deployments is a policy question (see regulatory section in TODO).

### 3.3 Antenna and placement

- The antenna system dominates performance and must be treated as a first-class design element.
- Options:
  - Rugged monopole/whip (simple, broad bandwidth).
  - Patch antenna (more controlled pattern, can be integrated under a radome).
- Provide a **mechanically constrained antenna mount** to prevent coax fatigue.

### 3.4 Power subsystem

- Power sources:
  - Primary cells (Li‑SOCl₂) for long shelf life and cold performance (with caveats).
  - Rechargeable (Li‑ion / LiFePO₄) + solar where practical.
- Include:
  - High-efficiency buck/boost with low quiescent current.
  - Ideal diode / ORing for multiple sources.
  - Accurate coulomb counting (optional) or at least voltage + temperature.
- Firmware: deep sleep with periodic beaconing + event-driven wake.

### 3.5 Enclosure / environmental

- **Dust sealing:** gaskets, labyrinth seals, pressure-equalization strategy (Earth). Lunar dust is abrasive and electrostatic; assume aggressive ingress protection.
- **Thermal design:**
  - Conductive coupling from hot spots to enclosure.
  - Insulation and thermal mass to smooth cycles.
  - For vacuum, convection is absent; design for conduction + radiation.
- **Connectors:** minimize; prefer sealed connectors; include strain relief.

## 4) Radiation and reliability strategy (planetary case)

### 4.1 Practical radiation approach

- Use **shielding** (e.g., aluminum enclosure) and **component selection** (industrial temp, good process maturity).
- Add **system-level tolerance**:
  - Periodic reboot / scrubbing.
  - ECC where available.
  - Watchdog + safe-mode.

### 4.2 Single-event effects (SEEs)

- Expect occasional bit flips.
- Mitigations:
  - CRCs on stored state.
  - Double-buffered config.
  - Avoid complex filesystems where possible.

### 4.3 Redundancy

- Network-level redundancy (many nodes) is often cheaper than per-node rad-hardening.
- Consider “hot spare” nodes that are normally asleep.

## 5) Operational modes (example)

- **Beacon mode:** periodic health + routing beacons.
- **Pager mode:** receive window schedule + urgent broadcast.
- **Relay mode:** forward messages when awake; duty-cycle aware.
- **Maintenance mode:** local access for configuration and logs.

## 6) Open questions / next design steps

1. Define **message types and priorities** (life-critical alerts vs. bulk logs).
2. Choose a **routing strategy** compatible with long sleep cycles.
3. Define the **thermal envelope** and power budget for the target site.
4. Prototype enclosure concepts (dust, connectors, antenna mounting).
5. Decide whether nodes must be **field-repairable** with gloves/EVA constraints.

## 7) Suggested acceptance tests (early)

- Thermal cycling + cold start tests.
- Dust ingress / abrasive exposure (as close as practical).
- Vibration/shock (transport/landing proxy).
- Long-duration soak with periodic messaging.
- Fault injection: brownouts, random resets, corrupt config.
