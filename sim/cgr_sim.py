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
        
    def find_next_hop(self, bundle: Bundle, current_t: float) -> Optional[int]:
        # Simple earliest-delivery-time heuristic
        best_hop = None
        best_time = float('inf')
        
        # Filter contacts valid after current_t
        valid_contacts = [c for c in self.contacts if c.source == self.node_id and c.end_t > current_t]
        
        for c in valid_contacts:
            # If direct contact to destination
            if c.dest == bundle.dest:
                start = max(current_t, c.start_t)
                xmit_time = bundle.size / c.datarate
                if start + xmit_time <= c.end_t:
                    return c.dest
            
            # Note: A real CGR would recursively look for paths.
            # This is a 'basic' CGR implementation.
        
        return None

def main():
    print("Basic CGR Simulation Prototype")
    # To be expanded in future sessions
    pass

if __name__ == "__main__":
    main()
