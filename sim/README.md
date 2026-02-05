# Mesh Simulation (Prototype)

This folder contains a **small, dependency-free** simulator for exploring how node density and terrain attenuation affect **mesh reachability**.

It is deliberately simple: it uses a FSPL-anchored log-distance path loss model plus optional obstacle rectangles that add dB of attenuation if a link crosses them. Optionally, you can add per-link Gaussian "shadowing" to explore variability.

## Run

From the repo root:

```bash
python3 sim/mesh_sim.py --help

python3 sim/mesh_sim.py --nodes 50 --width 2000 --height 2000 \
  --freq-mhz 868 --tx-power-dbm 14 --sensitivity-dbm -130

# Add extra clutter loss (path loss exponent) + variability (shadowing)
python3 sim/mesh_sim.py --nodes 50 --width 2000 --height 2000 \
  --freq-mhz 868 --tx-power-dbm 14 --sensitivity-dbm -130 \
  --path-loss-exp 3.0 --shadowing-sigma-db 4

# JSON output (easier to plot)
python3 sim/mesh_sim.py --nodes 80 --scenario sim/scenarios/ridges.json --json
```

## Output metrics

- `reachable_pair_fraction`: fraction of ordered node pairs (A→B) that have a multi-hop route
- `avg_hops_reachable`: average hop count for reachable ordered pairs
- `largest_out_component_fraction`: max fraction of nodes reachable from any single node (includes itself)

## Notes / limitations

- Does **not** model MAC-layer collisions, airtime, duty cycle, or routing overhead.
- Uses FSPL; real LoRa links are often dominated by terrain/clutter losses.
- Obstacles are a crude proxy for ridges/walls; use as a knob, not a prediction.
