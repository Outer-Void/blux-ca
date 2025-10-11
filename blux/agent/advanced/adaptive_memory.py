from datetime import datetime

class AdaptiveMemory:
    """
    Implements advanced adaptive memory for BLUX-cA agents.
    Features:
    - Long-term and weighted memory
    - Reinforcement loops based on interactions
    - Memory decay for outdated or irrelevant entries
    """
    def __init__(self, decay_rate=0.01):
        self.memory_store = []
        self.decay_rate = decay_rate  # Amount memory weight decays per cycle

    def store(self, entry, weight=1.0):
        """
        Stores a memory entry with optional weight.
        Entry format: {'input': str, 'user_type': str, 'decision': str, 'timestamp': datetime, 'weight': float}
        """
        memory_entry = {
            "input": entry.get("input", ""),
            "user_type": entry.get("user_type", "unknown"),
            "decision": entry.get("decision", ""),
            "timestamp": datetime.now(),
            "weight": weight
        }
        self.memory_store.append(memory_entry)
        self.reinforce(memory_entry)

    def recall(self, filter_fn=None, top_n=None):
        """
        Returns filtered memory, optionally limited to top_n weighted entries.
        """
        memory = self.memory_store
        if filter_fn:
            memory = [e for e in memory if filter_fn(e)]
        memory = sorted(memory, key=lambda x: x["weight"], reverse=True)
        if top_n:
            memory = memory[:top_n]
        return memory

    def reinforce(self, entry, factor=0.1):
        """
        Adjusts the weight of memory entries based on reinforcement.
        Placeholder: reinforcement logic can be updated based on user success or relevance.
        """
        entry["weight"] += factor
        self.apply_decay()

    def apply_decay(self):
        """
        Applies decay to all memory entries to reduce relevance of older/unimportant items.
        """
        for entry in self.memory_store:
            entry["weight"] *= (1 - self.decay_rate)

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