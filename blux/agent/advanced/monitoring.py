import time
from threading import Thread

class MonitoringDashboard:
    """
    Real-time monitoring dashboard for BLUX-cA agents.
    Features:
    - Live console monitoring
    - Optional threaded update
    - Integration with SecureController
    """
    def __init__(self, controller):
        self.controller = controller
        self.running = False

    def show_status(self):
        agents = getattr(self.controller.registry, "agents", {})
        adaptors = getattr(self.controller.registry, "adaptors", {})
        evaluators = getattr(self.controller.registry, "evaluators", {})
        print("=== BLUX-cA System Status ===")
        print(f"Agents registered: {list(agents.keys())}")
        print(f"Adaptors registered: {list(adaptors.keys())}")
        print(f"Evaluators registered: {list(evaluators.keys())}")
        print("==============================")

    def live_monitor(self, interval=5):
        """
        Continuously display system status every `interval` seconds.
        """
        self.running = True
        try:
            while self.running:
                self.show_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Monitoring stopped.")

    def start_threaded_monitor(self, interval=5):
        """
        Starts monitoring in a separate thread, allowing main process to continue.
        """
        thread = Thread(target=self.live_monitor, args=(interval,), daemon=True)
        thread.start()
        return thread

    def stop_monitoring(self):
        self.running = False

# Example usage:
if __name__ == "__main__":
    from blux.orchestrator.secure.secure_controller import SecureController
    from blux.orchestrator.registry import Registry

    # Dummy controller for monitoring demo
    class DummyController:
        def __init__(self):
            self.registry = Registry()
            # Add some dummy agents/adaptors/evaluators
            self.registry.agents = {"Agent_A": None, "Agent_B": None}
            self.registry.adaptors = {"DummyAdaptor": None}
            self.registry.evaluators = {"PythonEvaluator": None}

    controller = DummyController()
    dashboard = MonitoringDashboard(controller)
    dashboard.show_status()
    # Optional: dashboard.start_threaded_monitor(interval=2)