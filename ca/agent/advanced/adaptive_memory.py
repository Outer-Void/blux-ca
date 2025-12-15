# blux/agent/advanced/adaptive_memory.py

import time
from threading import Lock

class AdaptiveMemory:
    """
    Thread-safe adaptive memory for BLUX-cA agents.
    Supports decay, priority weighting, tag-based recall, and checkpointing.
    """

    def __init__(self):
        self.memory_store = {}
        self.lock = Lock()

    def add(self, key, value, user_type="default", priority=1, tags=None):
        if tags is None:
            tags = []
        with self.lock:
            self.memory_store[key] = {
                "value": value,
                "user_type": user_type,
                "priority": priority,
                "tags": tags,
                "timestamp": time.time()
            }

    def recall(self, key, decay_rate=0.001):
        with self.lock:
            data = self.memory_store.get(key)
            if not data:
                return None
            age = time.time() - data["timestamp"]
            weight = max(0, data["priority"] * (1 - decay_rate * age))
            return {"value": data["value"], "weight": weight, "tags": data["tags"]}

    def recall_by_tag(self, tag):
        with self.lock:
            return [
                {key: data}
                for key, data in self.memory_store.items()
                if tag in data['tags']
            ]

    def save_checkpoint(self, file_path='memory_checkpoint.json'):
        with self.lock:
            with open(file_path, 'w') as f:
                json.dump(self.memory_store, f, indent=2)

    def load_checkpoint(self, file_path='memory_checkpoint.json'):
        try:
            with self.lock:
                with open(file_path, 'r') as f:
                    self.memory_store = json.load(f)
        except FileNotFoundError:
            self.memory_store = {}

    def apply_decay(self):
        """Applies decay to all memory entries to reduce relevance of older/unimportant items."""
        for entry in self.memory_store.values():
            entry['weight'] *= (1 - self.decay_rate)

    def summarize_memory(self):
        """
        Returns a simple summary of memory weights and top entries.
        """
        top_entries = self.recall(top_n=5)
        summary = [{"input": e["input"], "weight": e["weight"]} for e in top_entries]
        return summary

# Example usage:
if __name__ == "__main__":
    am = AdaptiveMemory()
    am.store({"input": "I need help", "user_type": "struggler", "decision": "provide guidance"})
    am.store({"input": "Ignore this", "user_type": "indulgent", "decision": "set boundary"})
    print("Top memory entries:", am.summarize_memory())
