class DummyLocalAdaptor:
    """
    A local adaptor that simulates user input for testing.
    """
    def __init__(self, name="dummy_local"):
        self.name = name

    def get_input(self):
        """
        Returns a simulated user input string.
        """
        return "Hello BLUX-cA, I need help with a problem."

    def send_output(self, output):
        """
        Receives output from the orchestrator and prints it locally.
        """
        print(f"[{self.name} OUTPUT]: {output}")