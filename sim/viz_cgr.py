#!/usr/bin/env python3
"""viz_cgr.py

Visualizes Contact Graph Routing (CGR) contacts as a Gantt-style chart.
"""

import matplotlib.pyplot as plt
import argparse
from dataclasses import dataclass
from typing import List

@dataclass
class Contact:
    source: int
    dest: int
    start_t: float
    end_t: float
    datarate: float

def visualize_contacts(contacts: List[Contact]):
    # ASCII Visualization
    print("\n--- Contact Plan (ASCII Gantt) ---")
    pairs = sorted(list(set([(c.source, c.dest) for c in contacts])))
    max_t = max([c.end_t for c in contacts])
    width = 60 # character width
    
    for s, d in pairs:
        label = f"{s}->{d}".ljust(8)
        row = [" "] * width
        pair_contacts = [c for c in contacts if c.source == s and c.dest == d]
        for c in pair_contacts:
            start_idx = int((c.start_t / max_t) * (width - 1))
            end_idx = int((c.end_t / max_t) * (width - 1))
            for i in range(start_idx, end_idx + 1):
                row[i] = "█"
        print(f"{label} |{''.join(row)}|")
    
    # Timeline
    timeline = " " * 8 + " 0" + "-" * (width - 4) + f" {int(max_t)}"
    print(timeline)

if __name__ == "__main__":
    # Example contacts (matching cgr_sim.py test case)
    test_contacts = [
        Contact(source=0, dest=1, start_t=0, end_t=10, datarate=1000),
        Contact(source=1, dest=2, start_t=20, end_t=30, datarate=1000),
        Contact(source=0, dest=3, start_t=0, end_t=20, datarate=100),
        Contact(source=3, dest=2, start_t=5, end_t=25, datarate=100),
        Contact(source=0, dest=2, start_t=50, end_t=60, datarate=500)
    ]
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="contact_gantt.png")
    args = parser.parse_args()
    
    try:
        visualize_contacts(test_contacts)
    except Exception as e:
        print(f"Error generating visualization: {e}")
