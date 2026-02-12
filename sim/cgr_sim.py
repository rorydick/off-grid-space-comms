#!/usr/bin/env python3
"""cgr_sim.py

A simple Contact Graph Routing (CGR) simulator.
Builds on top of basic mesh connectivity concepts but introduces time-varying links.
"""

import math
import argparse
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Contact:
    source: int
    dest: int
    start_t: float
    end_t: float
    datarate: float # bps

@dataclass
class Bundle:
    id: int
    source: int
    dest: int
    size: float # bits
    creation_t: float
    deadline_t: float

class CGRRouter:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.contacts: List[Contact] = []
        
    def add_contact(self, contact: Contact):
        self.contacts.append(contact)
        
    def find_path(self, bundle: Bundle, current_t: float) -> Optional[Tuple[List[int], float]]:
        """
        Find a path (list of node IDs) and the estimated arrival time.
        Implements Dijkstra's algorithm over the Contact Graph.
        """
        import heapq

        # (arrival_time, current_node, path_taken)
        queue = [(current_t, self.node_id, [self.node_id])]
        best_arrival = {self.node_id: current_t}

        while queue:
            t, u, path = heapq.heappop(queue)

            if u == bundle.dest:
                return path, t

            if t > best_arrival.get(u, float('inf')):
                continue

            for c in self.contacts:
                if c.source == u and c.dest not in path:
                    xmit_duration = bundle.size / c.datarate
                    earliest_start = max(t, c.start_t)
                    arrival_t = earliest_start + xmit_duration

                    if arrival_t <= c.end_t and arrival_t <= bundle.deadline_t:
                        if arrival_t < best_arrival.get(c.dest, float('inf')):
                            best_arrival[c.dest] = arrival_t
                            heapq.heappush(queue, (arrival_t, c.dest, path + [c.dest]))
        
        return None

def main():
    parser = argparse.ArgumentParser(description="Contact Graph Routing (CGR) Simulator")
    parser.add_argument("--bundle-size", type=float, default=1000, help="Bundle size in bits")
    args = parser.parse_args()

    print(f"--- CGR Multi-Hop Simulation ---")
    
    # Define a complex time-varying scenario:
    contacts = [
        # Path A: Fast but delayed
        Contact(source=0, dest=1, start_t=0, end_t=10, datarate=1000),
        Contact(source=1, dest=2, start_t=20, end_t=30, datarate=1000),
        
        # Path B: Slow but immediate
        Contact(source=0, dest=3, start_t=0, end_t=20, datarate=100),
        Contact(source=3, dest=2, start_t=5, end_t=25, datarate=100),

        # Path C: Direct but very late
        Contact(source=0, dest=2, start_t=50, end_t=60, datarate=500)
    ]
    
    bundle = Bundle(id=1, source=0, dest=2, size=args.bundle_size, creation_t=0, deadline_t=100)
    
    router = CGRRouter(node_id=0)
    for c in contacts:
        router.add_contact(c)
        
    print(f"Bundle: {bundle.size} bits, {bundle.source} -> {bundle.dest}")
    result = router.find_path(bundle, current_t=0)
    
    if result:
        path, arrival = result
        print(f"SUCCESS: Found path: {' -> '.join(map(str, path))}")
        print(f"Estimated Arrival Time: {arrival:.2f}")
    else:
        print("FAILURE: No valid path found within deadline.")

if __name__ == "__main__":
    main()
