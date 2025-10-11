"""
Script to create new log entries or reflections in the BLUX-cA project.
"""

import os
from datetime import datetime

REFLECTIONS_DIR = os.path.join(os.path.dirname(__file__), "../reflections")

def create_entry(title, content):
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{date_str}_{title.replace(' ', '_')}.md"
    path = os.path.join(REFLECTIONS_DIR, filename)

    os.makedirs(REFLECTIONS_DIR, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"# {title}\n\n{content}\n")

    print(f"Created reflection entry: {filename}")

# Example usage
if __name__ == "__main__":
    create_entry("Sample Entry", "This is a sample reflection for BLUX-cA.")