#!/usr/bin/env python3
"""mesh_sim.py

A tiny, dependency-free mesh-network propagation simulator.

Goal
----
Provide a *simple* model that helps reason about:
- node density vs. connectivity
- hop count / reachability
- effect of terrain/obstacle attenuation on LoRa-class links
- energy consumption and congestion (multi-hop)

This is not a RF-accurate channel model. It is intended as a lightweight
exploration tool for early architecture discussions.

Model
-----
- Nodes live in 2D (meters)
- Link budget is estimated with a log-distance path loss model (FSPL-anchored) + optional
  obstacle losses (rectangles that add dB if the line-of-sight intersects), plus optional
  per-link Gaussian shadowing.
- A directed edge A->B exists if: tx_power_dbm - path_loss_db >= sensitivity_dbm

Usage
-----
  python3 sim/mesh_sim.py --help

Examples
--------
  # 50 nodes in a 2km x 2km area, 868 MHz LoRa-ish
  python3 sim/mesh_sim.py --nodes 50 --width 2000 --height 2000 --freq-mhz 868 \
    --tx-power-dbm 14 --sensitivity-dbm -130

  # Add two "ridges" with 12 dB attenuation each
  python3 sim/mesh_sim.py --nodes 80 --scenario sim/scenarios/ridges.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RectObstacle:
    """Axis-aligned rectangle obstacle with fixed attenuation (dB)."""

    x1: float
    y1: float
    x2: float
    y2: float
    loss_db: float

    def normalise(self) -> "RectObstacle":
        return RectObstacle(
            x1=min(self.x1, self.x2),
            y1=min(self.y1, self.y2),
            x2=max(self.x1, self.x2),
            y2=max(self.y1, self.y2),
            loss_db=self.loss_db,
        )


def fspl_db(distance_m: float, freq_mhz: float) -> float:
    """Free-space path loss in dB.

    FSPL(dB) = 32.44 + 20 log10(d_km) + 20 log10(f_MHz)

    Clamp distance to avoid log(0).
    """

    d_km = max(distance_m, 0.1) / 1000.0
    return 32.44 + 20.0 * math.log10(d_km) + 20.0 * math.log10(freq_mhz)


def log_distance_path_loss_db(
    distance_m: float,
    *,
    freq_mhz: float,
    path_loss_exp: float,
    ref_distance_m: float = 1.0,
) -> float:
    """Log-distance path loss model anchored to FSPL at a reference distance.

    This generalises FSPL (n=2) to rough "clutter" environments where loss grows
    faster with distance.

    PL(d) = PL(d0) + 10 n log10(d/d0)

    Notes:
    - For path_loss_exp=2.0 and ref_distance_m=1.0, this closely matches FSPL.
    - This is still a crude model; use for qualitative sensitivity analysis.
    """

    d = max(distance_m, ref_distance_m)
    pl_ref = fspl_db(ref_distance_m, freq_mhz)
    return pl_ref + 10.0 * path_loss_exp * math.log10(d / ref_distance_m)


def segment_intersects_rect(a: Tuple[float, float], b: Tuple[float, float], r: RectObstacle) -> bool:
    """Liang–Barsky line clipping to test intersection with axis-aligned rectangle."""

    x0, y0 = a
    x1, y1 = b
    dx = x1 - x0
    dy = y1 - y0

    p = [-dx, dx, -dy, dy]
    q = [x0 - r.x1, r.x2 - x0, y0 - r.y1, r.y2 - y0]

    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False
        else:
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return False
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return False
                if t < u2:
                    u2 = t
    return True


def obstacle_loss_db(a: Tuple[float, float], b: Tuple[float, float], obstacles: Sequence[RectObstacle]) -> float:
    loss = 0.0
    for ob in obstacles:
        if segment_intersects_rect(a, b, ob):
            loss += ob.loss_db
    return loss


@dataclass
class Node:
    """Represents a mesh node with position and power state."""
    id: int
    x: float
    y: float
    energy_consumed_joules: float = 0.0
    messages_handled: int = 0

    def consume(self, joules: float):
        self.energy_consumed_joules += joules

    def handle_msg(self):
        self.messages_handled += 1


def build_graph(
    nodes: Sequence[Node],
    *,
    freq_mhz: float,
    tx_power_dbm: float,
    sensitivity_dbm: float,
    obstacles: Sequence[RectObstacle],
    path_loss_exp: float = 2.0,
    shadowing_sigma_db: float = 0.0,
    rng: Optional[random.Random] = None,
) -> List[List[int]]:
    """Return adjacency list for directed reachability."""

    n = len(nodes)
    adj: List[List[int]] = [[] for _ in range(n)]
    if rng is None:
        rng = random

    for i in range(n):
        ni = nodes[i]
        for j in range(n):
            if i == j:
                continue
            nj = nodes[j]
            d = math.hypot(nj.x - ni.x, nj.y - ni.y)

            path_loss = log_distance_path_loss_db(
                d,
                freq_mhz=freq_mhz,
                path_loss_exp=path_loss_exp,
            )
            path_loss += obstacle_loss_db((ni.x, ni.y), (nj.x, nj.y), obstacles)
            if shadowing_sigma_db > 0.0:
                path_loss += rng.gauss(0.0, shadowing_sigma_db)

            rx_dbm = tx_power_dbm - path_loss
            if rx_dbm >= sensitivity_dbm:
                adj[i].append(j)
    return adj


def run_broadcast_sim(
    nodes: List[Node],
    adj: List[List[int]],
    start_node_id: int,
    tx_energy_j: float,
    rx_energy_j: float,
) -> List[Optional[int]]:
    """Simulate a single broadcast flooding the network and track energy/congestion."""
    n = len(nodes)
    dist: List[Optional[int]] = [None] * n
    dist[start_node_id] = 0
    
    # Start node TX energy
    nodes[start_node_id].consume(tx_energy_j)
    nodes[start_node_id].handle_msg()
    
    q = [start_node_id]
    qi = 0
    while qi < len(q):
        u_idx = q[qi]
        qi += 1
        du = dist[u_idx]
        
        for v_idx in adj[u_idx]:
            # Every node in range consumes RX energy to listen/process
            nodes[v_idx].consume(rx_energy_j)
            
            if dist[v_idx] is None:
                dist[v_idx] = du + 1
                # If it's a new hop, this node re-broadcasts
                nodes[v_idx].consume(tx_energy_j)
                nodes[v_idx].handle_msg()
                q.append(v_idx)
    return dist


def connectivity_metrics(nodes: List[Node], adj: Sequence[Sequence[int]], tx_j: float, rx_j: float) -> Dict[str, float]:
    n = len(adj)
    if n == 0:
        return {
            "nodes": 0,
            "reachable_pair_fraction": 0.0,
            "avg_hops_reachable": 0.0,
            "largest_out_component_fraction": 0.0,
            "avg_link_density": 0.0,
            "max_hops": 0.0,
            "total_energy_j": 0.0,
            "avg_energy_per_broadcast_j": 0.0,
            "max_messages_per_node": 0.0,
        }

    reachable_pairs = 0
    reachable_hops_sum = 0
    max_reached_from_any = 0
    max_hops_overall = 0
    total_edges = 0
    
    # Reset state for metric calculation (we'll run N broadcasts)
    for node in nodes:
        node.energy_consumed_joules = 0.0
        node.messages_handled = 0

    for i in range(n):
        total_edges += len(adj[i])
        dist = run_broadcast_sim(nodes, list(adj), i, tx_j, rx_j)
        reached = 0
        for j in range(n):
            if i == j:
                continue
            d = dist[j]
            if d is not None:
                reached += 1
                reachable_pairs += 1
                reachable_hops_sum += d
                if d > max_hops_overall:
                    max_hops_overall = d
        if reached > max_reached_from_any:
            max_reached_from_any = reached

    total_pairs = n * (n - 1)
    frac = reachable_pairs / total_pairs if total_pairs else 0.0
    avg_hops = reachable_hops_sum / reachable_pairs if reachable_pairs else 0.0
    largest_out_component = (max_reached_from_any + 1) / n
    avg_link_density = total_edges / n if n > 0 else 0.0
    
    total_energy = sum(node.energy_consumed_joules for node in nodes)
    avg_energy_per_broadcast = total_energy / n if n > 0 else 0.0
    max_msgs = max(node.messages_handled for node in nodes) if nodes else 0

    return {
        "nodes": float(n),
        "reachable_pair_fraction": frac,
        "avg_hops_reachable": avg_hops,
        "largest_out_component_fraction": largest_out_component,
        "avg_link_density": avg_link_density,
        "max_hops": float(max_hops_overall),
        "total_energy_j": total_energy,
        "avg_energy_per_broadcast_j": avg_energy_per_broadcast,
        "max_messages_per_node": float(max_msgs),
    }


def load_scenario(path: Path) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Scenario JSON must be an object")
    return data


def parse_obstacles(raw: object) -> List[RectObstacle]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("obstacles must be a list")
    obs: List[RectObstacle] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each obstacle must be an object")
        ob = RectObstacle(
            x1=float(item["x1"]),
            y1=float(item["y1"]),
            x2=float(item["x2"]),
            y2=float(item["y2"]),
            loss_db=float(item.get("loss_db", item.get("lossDb", 0.0))),
        ).normalise()
        obs.append(ob)
    return obs


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Simple mesh propagation/connectivity simulator")
    ap.add_argument("--nodes", type=int, default=50, help="number of nodes")
    ap.add_argument("--width", type=float, default=2000.0, help="area width (m)")
    ap.add_argument("--height", type=float, default=2000.0, help="area height (m)")
    ap.add_argument("--seed", type=int, default=1, help="RNG seed")
    ap.add_argument("--freq-mhz", type=float, default=868.0, help="carrier frequency (MHz)")
    ap.add_argument("--tx-power-dbm", type=float, default=14.0, help="TX power (dBm)")
    ap.add_argument("--sensitivity-dbm", type=float, default=-130.0, help="RX sensitivity (dBm)")
    ap.add_argument(
        "--path-loss-exp",
        type=float,
        default=2.0,
        help="log-distance path loss exponent n (2=free-space-like, 2.7-4=clutter)",
    )
    ap.add_argument(
        "--shadowing-sigma-db",
        type=float,
        default=0.0,
        help="optional per-link Gaussian shadowing sigma (dB); 0 disables",
    )
    ap.add_argument("--tx-energy-j", type=float, default=0.1, help="Energy consumed per transmission (Joules)")
    ap.add_argument("--rx-energy-j", type=float, default=0.01, help="Energy consumed per reception/listen (Joules)")
    ap.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="optional scenario JSON (overrides width/height/obstacles if provided)",
    )
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON only")

    args = ap.parse_args(argv)

    width = args.width
    height = args.height
    obstacles: List[RectObstacle] = []

    if args.scenario:
        scen = load_scenario(Path(args.scenario))
        width = float(scen.get("width_m", width))
        height = float(scen.get("height_m", height))
        obstacles = parse_obstacles(scen.get("obstacles"))

    rng = random.Random(args.seed)
    nodes = [Node(id=i, x=rng.random() * width, y=rng.random() * height) for i in range(args.nodes)]

    adj = build_graph(
        nodes,
        freq_mhz=args.freq_mhz,
        tx_power_dbm=args.tx_power_dbm,
        sensitivity_dbm=args.sensitivity_dbm,
        obstacles=obstacles,
        path_loss_exp=args.path_loss_exp,
        shadowing_sigma_db=args.shadowing_sigma_db,
        rng=rng,
    )
    metrics = connectivity_metrics(nodes, adj, args.tx_energy_j, args.rx_energy_j)

    out = {
        "params": {
            "nodes": args.nodes,
            "width_m": width,
            "height_m": height,
            "seed": args.seed,
            "freq_mhz": args.freq_mhz,
            "tx_power_dbm": args.tx_power_dbm,
            "sensitivity_dbm": args.sensitivity_dbm,
            "path_loss_exp": args.path_loss_exp,
            "shadowing_sigma_db": args.shadowing_sigma_db,
            "tx_energy_j": args.tx_energy_j,
            "rx_energy_j": args.rx_energy_j,
            "obstacles": [ob.__dict__ for ob in obstacles],
        },
        "metrics": metrics,
    }

    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    print("Mesh sim summary")
    print("----------------")
    p = out["params"]
    print(f"nodes: {p['nodes']}  area: {p['width_m']}m x {p['height_m']}m  freq: {p['freq_mhz']} MHz")
    print(
        f"tx_power: {p['tx_power_dbm']} dBm  sensitivity: {p['sensitivity_dbm']} dBm  "
        f"n: {p['path_loss_exp']}  shadow_sigma: {p['shadowing_sigma_db']} dB  seed: {p['seed']}"
    )
    if obstacles:
        print(f"obstacles: {len(obstacles)} (rectangles w/ attenuation)")
    m = out["metrics"]
    print(f"reachable pair fraction: {m['reachable_pair_fraction']:.3f}")
    print(f"avg hops (reachable pairs): {m['avg_hops_reachable']:.2f}")
    print(f"max hops observed: {m['max_hops']:.0f}")
    print(f"avg link density (edges/node): {m['avg_link_density']:.2f}")
    print(f"largest out-component fraction: {m['largest_out_component_fraction']:.3f}")
    print(f"avg energy per broadcast: {m['avg_energy_per_broadcast_j']:.3f} J")
    print(f"max messages per node (congestion proxy): {m['max_messages_per_node']:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
