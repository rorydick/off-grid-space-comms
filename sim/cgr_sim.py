#!/usr/bin/env python3
"""cgr_sim.py

A simple Contact Graph Routing (CGR) simulator.
Builds on top of basic mesh connectivity concepts but introduces time-varying links.
"""

import json
import math
import argparse
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import IntEnum

class Priority(IntEnum):
    BULK = 0
    NORMAL = 1
    EXPEDITED = 2

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
    priority: Priority = Priority.NORMAL
    fragments: List['BundleFragment'] = None

@dataclass
class BundleFragment:
    bundle_id: int
    offset: int
    size: float
    arrival_t: float = -1.0

@dataclass
class CGRNodeState:
    node_id: int
    current_storage_bits: float = 0.0
    energy_consumed_joules: float = 0.0

class CGRRouter:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.contacts: List[Contact] = []
        self.storage_limit = float('inf')
        self.current_storage = 0
        self.queue: List[Bundle] = []
        
        # Energy model: 0.1 mJ per bit stored per second (placeholder)
        self.storage_power_w = 0.0001 
        self.last_update_t = 0.0
        self.energy_joules = 0.0
        
    def add_contact(self, contact: Contact):
        self.contacts.append(contact)

    def update_energy(self, current_t: float):
        """Update energy consumption based on time elapsed and storage."""
        dt = max(0, current_t - self.last_update_t)
        # Power proportional to bits stored (simple model)
        self.energy_joules += self.current_storage * self.storage_power_w * dt
        self.last_update_t = current_t

    def enqueue_bundle(self, bundle: Bundle):
        """Add bundle to priority queue."""
        if self.current_storage + bundle.size > self.storage_limit:
            print(f"  DROP: Bundle {bundle.id} exceeds storage limit.")
            return
        
        self.update_energy(bundle.creation_t)
        self.queue.append(bundle)
        self.current_storage += bundle.size
        # Sort by priority (high first), then deadline (earliest first)
        self.queue.sort(key=lambda b: (-b.priority, b.deadline_t))

    def process_queue(self, current_t: float):
        """Attempt to route all queued bundles in priority order."""
        self.update_energy(current_t)
        print(f"\n--- Processing Queue at t={current_t:.2f} ---")
        print(f"Storage: {self.current_storage} bits | Energy: {self.energy_joules:.4f} J")
        delivered = []
        for bundle in self.queue:
            print(f"Routing Bundle {bundle.id} (Priority: {bundle.priority.name}): {bundle.size} bits from {bundle.source} to {bundle.dest}")
            result = self.find_path(bundle, current_t)
            if result:
                path, arrival = result
                print(f"  SUCCESS (Single): {' -> '.join(map(str, path))} @ {arrival:.2f}")
                delivered.append(bundle)
            else:
                frags = self.find_path_fragmented(bundle, current_t)
                if frags:
                    print(f"  SUCCESS (Fragmented): {len(frags)} fragments")
                    delivered.append(bundle)
                else:
                    print("  STAYING IN QUEUE: No path found.")
        
        for b in delivered:
            self.queue.remove(b)
            self.current_storage -= b.size
        
        self.update_energy(current_t)
        print(f"Final Storage: {self.current_storage} bits | Final Energy: {self.energy_joules:.4f} J")
        
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
                            # Note: This is an approximation. A more precise implementation
                            # would split the contact window or track bytes_sent.
                            # Fixing logic: t + (actual_send / c.datarate) is the consumption time.
                            xmit_time = actual_send / c.datarate
                            c.start_t = max(c.start_t, t + xmit_time)

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
    parser.add_argument("--scenario", type=str, help="Path to contact plan JSON")
    parser.add_argument("--storage", type=float, default=float('inf'), help="Node storage limit in bits")
    args = parser.parse_args()

    router = CGRRouter(node_id=0)
    router.storage_limit = args.storage

    if args.scenario:
        with open(args.scenario, 'r') as f:
            data = json.load(f)
            for c_data in data.get('contacts', []):
                router.add_contact(Contact(**c_data))
            
            for b_data in data.get('bundles', []):
                # Handle priority conversion if string
                if 'priority' in b_data and isinstance(b_data['priority'], str):
                    b_data['priority'] = Priority[b_data['priority'].upper()]
                router.enqueue_bundle(Bundle(**b_data))
            
            if not router.queue:
                print("No bundles found in scenario.")
                return
            
            router.process_queue(0.0) # Start sim at t=0
        return

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
    
    router = CGRRouter(node_id=0)
    router.storage_limit = 2000 # bits
    for c in contacts:
        router.add_contact(c)

    # Add three bundles: one Bulk, one Expedited, one that exceeds storage
    b1 = Bundle(id=1, source=0, dest=2, size=1000, creation_t=0, deadline_t=100, priority=Priority.BULK)
    b2 = Bundle(id=2, source=0, dest=2, size=500, creation_t=10, deadline_t=100, priority=Priority.EXPEDITED)
    b3 = Bundle(id=3, source=0, dest=2, size=1000, creation_t=15, deadline_t=100, priority=Priority.NORMAL)
    
    print("\n--- Testing Storage & Energy & Priority ---")
    router.enqueue_bundle(b1)
    router.enqueue_bundle(b2)
    router.enqueue_bundle(b3) # Should be dropped or stay if room?
    
    router.process_queue(current_t=20)

if __name__ == "__main__":
    main()
