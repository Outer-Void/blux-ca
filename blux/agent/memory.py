class Memory:
    """
    Handles long-term and session memory storage.
    """
    def __init__(self):
        self.session_memory = []
        self.long_term_memory = []

    def store(self, user_input, user_type, decision):
        entry = {
            "input": user_input,
            "user_type": user_type,
            "decision": decision
        }
        self.session_memory.append(entry)
        # Placeholder for consented long-term memory
        self.long_term_memory.append(entry)

    def recall_session(self):
        return self.session_memory

    def recall_long_term(self):
        return self.long_term_memory