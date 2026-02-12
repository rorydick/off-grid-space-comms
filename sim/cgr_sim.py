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
    fragments: List['BundleFragment'] = None

@dataclass
class BundleFragment:
    bundle_id: int
    offset: int
    size: float
    arrival_t: float = -1.0

class CGRRouter:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.contacts: List[Contact] = []
        
    def add_contact(self, contact: Contact):
        self.contacts.append(contact)
        
    def find_path_fragmented(self, bundle: Bundle, current_t: float) -> Optional[List[Tuple[List[int], float, float]]]:
        """
        Find paths for bundle fragments. If a single path can't carry the whole bundle,
        split it across available contacts.
        Returns a list of (path, arrival_t, size) tuples.
        """
        remaining_size = bundle.size
        fragment_plans = []
        
        # Simple greedy approach: find earliest delivery for any portion, repeat until size is 0
        while remaining_size > 0:
            import heapq
            # (arrival_time, current_node, path_taken, max_capacity_of_path)
            queue = [(current_t, self.node_id, [self.node_id], float('inf'))]
            best_arrival = {} # We don't use a simple best_arrival because we need to track capacity
            
            best_fragment_path = None
            best_fragment_arrival = float('inf')
            max_frag_size = 0
            
            # This is a simplification: we'll look for the BEST arrival for ANY size, 
            # then see how much we can push through it.
            # In real DTN, we might split across multiple concurrent contacts.
            
            queue = [(current_t, self.node_id, [self.node_id], float('inf'))]
            while queue:
                t, u, path, cap = heapq.heappop(queue)
                
                if u == bundle.dest:
                    if t < best_fragment_arrival:
                        best_fragment_arrival = t
                        best_fragment_path = path
                        max_frag_size = cap
                    continue
                
                for c in self.contacts:
                    if c.source == u and c.dest not in path:
                        # Capacity of this contact in this window
                        contact_cap = (c.end_t - max(t, c.start_t)) * c.datarate
                        if contact_cap <= 0: continue
                        
                        earliest_start = max(t, c.start_t)
                        # We'll try to send as much as possible, up to remaining_size
                        send_size = min(remaining_size, contact_cap)
                        xmit_duration = send_size / c.datarate
                        arrival_t = earliest_start + xmit_duration
                        
                        if arrival_t <= c.end_t and arrival_t <= bundle.deadline_t:
                            path_cap = min(cap, contact_cap)
                            heapq.heappush(queue, (arrival_t, c.dest, path + [c.dest], path_cap))

            if best_fragment_path:
                actual_send = min(remaining_size, max_frag_size)
                fragment_plans.append((best_fragment_path, best_fragment_arrival, actual_send))
                remaining_size -= actual_send
                
                # Consume capacity from contacts used in this path
                for i in range(len(best_fragment_path)-1):
                    u_node = best_fragment_path[i]
                    v_node = best_fragment_path[i+1]
                    for c in self.contacts:
                        if c.source == u_node and c.dest == v_node:
                            # This is a bit rough, but let's shift start_t forward
                            # to simulate consumed time in the window
                            c.start_t = max(c.start_t, best_fragment_arrival) 

                if actual_send == 0: break 
            else:
                break
                
        return fragment_plans if remaining_size == 0 else None

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
    
    print("\n--- Standard CGR (Single Path) ---")
    result = router.find_path(bundle, current_t=0)
    if result:
        path, arrival = result
        print(f"SUCCESS: Found path: {' -> '.join(map(str, path))}")
        print(f"Estimated Arrival Time: {arrival:.2f}")
    else:
        print("FAILURE: No valid single path found within deadline (bundle too large for any one window?).")

    print("\n--- Fragmented CGR (Multi-Path/Window) ---")
    large_bundle = Bundle(id=2, source=0, dest=2, size=15000, creation_t=0, deadline_t=100)
    print(f"Large Bundle: {large_bundle.size} bits, {large_bundle.source} -> {large_bundle.dest}")
    fragments = router.find_path_fragmented(large_bundle, current_t=0)
    
    if fragments:
        print(f"SUCCESS: Delivered in {len(fragments)} fragments.")
        for i, (path, arrival, size) in enumerate(fragments):
            print(f"  Frag {i+1}: {size} bits via {' -> '.join(map(str, path))} arriving @ {arrival:.2f}")
    else:
        print("FAILURE: Could not deliver large bundle even with fragmentation.")

if __name__ == "__main__":
    main()
