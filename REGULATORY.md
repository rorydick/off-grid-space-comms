# Regulatory Considerations (Space + Earth)

This project looks at *off-grid* communications for two very different contexts:

1. **On Earth**: emergency/disaster communications and community resilience.
2. **In space / on the Moon / Mars**: local comms inside a settlement plus intermittent backhaul.

Regulatory constraints differ materially across these environments. This note is a starting point and is **not legal advice**.

## 1) Spectrum authorization: who grants permission?

### Earth (national regulators)

On Earth, transmit authority is granted by **national** regulators (e.g., FCC in the US, Ofcom in the UK, BNetzA in Germany). Even if hardware is identical, legality varies by country.

Common paths:

- **License-exempt ISM bands** (region-specific): e.g., 433 MHz, 868 MHz (EU), 902–928 MHz (US), 2.4 GHz.
  - Pros: fast deployment, no per-user license.
  - Cons: duty-cycle/EIRP limits; interference; regional fragmentation.
- **Amateur radio** (where allowed): attractive for experimentation but typically has **strict constraints** (see below).
- **Licensed land mobile / public safety** allocations: powerful for integration with emergency services, but access is constrained.

### Space (international coordination + national licensing)

Space radiocommunication is coordinated internationally under the **ITU Radio Regulations**, with filings made through an administration (a national regulator).

Key ideas:

- **You generally still need a license** (via a national administration) for space-to-Earth links.
- Space services (e.g., Space Operation Service, Space Research Service, Earth Exploration-Satellite Service) determine which allocations and rules apply.
- Even for lunar surface systems, any RF that can reach Earth or uses space services will typically involve ITU coordination.

Practical implication for this project: *a “Meshtastic-class” PHY is easy locally, but any path to Earth backhaul needs a licensing plan early.*

## 2) Amateur radio (ham): useful, but not a free pass

Amateur radio can be a useful framework for prototyping and community deployment, but it commonly includes restrictions such as:

- **No encryption / obscuring meaning** (with limited exceptions), which conflicts with modern “privacy by default” designs.
- **Non-commercial use** constraints.
- **Identification / callsign** requirements.

Design implication: if using ham bands for prototypes, plan a **separate, compliant “open” mode** and a pathway to **licensed non-ham** operations for production.

## 3) Equipment authorization and compliance

For Earth deployments, it is not enough to have spectrum rights: the *equipment* often needs approval.

Typical requirements:

- **EMC/EMI compliance** (spurious emissions, harmonics)
- **Regional certification** (e.g., FCC Part 15, CE/RED)
- **Antenna limits** and EIRP constraints depending on band and service

For space deployments, the concerns are different:

- **Electromagnetic compatibility** with other spacecraft/settlement systems
- **Radiation tolerance** (SEEs, TID)
- **Outgassing / materials** constraints (mission-specific)

## 4) Security + crypto export controls

If the system uses strong cryptography, consider:

- **Export controls** (e.g., US EAR, potential ITAR adjacency depending on integration)
- **Key management policy** (especially if emergency services are involved)

Design implication: the system should be architected so that *crypto policy is modular* (e.g., pluggable link layer / application layer security), with a clear compliance story.

## 5) Planetary protection and local settlement governance

For lunar/Martian habitats, there may be additional mission rules and governance policies:

- Planetary protection constraints (more relevant to Mars)
- Settlement-wide RF coordination (to manage interference and safety)
- Operational safety requirements (e.g., RF exposure limits, compatibility with medical devices)

## 6) Suggested next steps for this repo

1. Add a short **country/region matrix** for ISM band constraints (EU868 vs US915 vs others).
2. Identify **two regulatory-ready operational modes**:
   - (A) local, license-exempt mesh for settlement/disaster areas
   - (B) a licensed backhaul mode (satellite/DTN gateway)
3. For Earth emergency integration, map candidate standards and agencies (see `EMERGENCY_INTEGRATION.md`).

## References to pull in later

- ITU Radio Regulations / space service allocations (primary source)
- National regulator documentation (FCC/Ofcom/etc.)
- CE/RED and FCC equipment authorization guides
