# Integrating Off-Grid Comms with Emergency Services (Earth)

This note sketches integration patterns between an off-grid mesh/DTN system and formal emergency services. The goal is to avoid a “cool standalone gadget” and instead support *real workflows* (alerting, dispatch, triage, accountability).

## 1) Integration goals

A realistic integration target is not “full voice replacement,” but:

- **Alert injection**: push critical messages *into* the mesh when conventional infrastructure is impaired.
- **Incident reporting**: allow field users to submit structured incident reports (location, severity, needs).
- **Accountability**: track who has acknowledged an alert and where they last checked in.
- **Gatewaying**: bridge between the mesh and existing systems without forcing responders to install bespoke apps.

## 2) Gateway patterns

### A) Mesh ↔ SMS / Cellular gateway

**Pattern:** a field gateway node (battery + small solar) that listens on mesh and forwards to SMS/voice where service exists.

- Pros: minimal changes for responders (SMS works everywhere).
- Cons: depends on at least *some* cellular coverage; SMS is low bandwidth and may be delayed.

### B) Mesh ↔ Internet gateway (when available)

**Pattern:** gateway node with intermittent internet uplink (Starlink, DSL, surviving LTE) bridges to email/webhooks.

- Pros: supports richer payloads (forms, images, maps) when bandwidth exists.
- Cons: cybersecurity posture matters; gateway becomes a high-value node.

### C) Mesh ↔ Public safety radio interface (future)

**Pattern:** bridge to professional land mobile radio (LMR) systems (e.g., TETRA, P25).

- Pros: aligns with existing emergency comms.
- Cons: deep regulatory + vendor + encryption constraints; often requires agency buy-in.

### D) DTN store-carry-forward for “blackout corridors”

**Pattern:** messages are carried physically by mobile nodes (vehicles, drones) and delivered when contact occurs.

- Pros: works even with *zero* infrastructure.
- Cons: latency; requires operational procedures and training.

## 3) Information formats

To integrate well, messages should be structured enough to route and prioritize.

Suggested minimal schema (human + machine readable):

- **type**: alert | check-in | incident | resource | evac
- **priority**: info | urgent | life-safety
- **location**: lat/lon (if available) + free-text landmark
- **timestamp**: local + UTC if possible
- **sender**: pseudonymous ID + optional verified role
- **payload**: short text + optional attachments (when bandwidth allows)

A pragmatic choice is to use **JSON** with a compact profile, and define an “SMS rendering” fallback.

## 4) Identity, trust, and abuse resistance

Key challenge: in disasters, systems are vulnerable to spam/hoaxes.

Design options:

- **Signed messages** (public keys distributed ahead of time)
- **Role-based credentials** for authorized alert injection (e.g., local authority)
- **Rate limiting** + local moderation controls
- **“Quorum” confirmation** for high-impact broadcasts

## 5) Operational concepts (what responders actually do)

- **Pre-incident provisioning:** distribute nodes to wardens/volunteers; run periodic drills.
- **Activation:** incident commander authorizes broadcast keys; gateway nodes deployed.
- **Triage:** incident reports are aggregated at gateways; summary forwarded to command.
- **Recovery:** after infrastructure returns, sync logs and verify message delivery.

## 6) Suggested next steps for this repo

1. Define a minimal **message schema** and a small set of **priority rules**.
2. Add a “gateway node” concept to `ARCHITECTURE.md` (threat model + power budget).
3. (Optional) Extend `sim/mesh_sim.py` to model a **gateway to infrastructure** node and measure coverage/latency tradeoffs.
