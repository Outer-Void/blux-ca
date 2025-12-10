# blux/agent/advanced/monitoring.py

import logging
import json
import time
from threading import Lock, Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BLUX-cA-Monitor")

class AgentMonitor:
    """
    Monitors BLUX-cA agent actions:
    - Input processing
    - Memory updates
    - Reasoning/strategy decisions
    - Audit compliance
    """

    def __init__(self, log_file="blux_agent.log"):
        self.log_file = log_file
        self.lock = Lock()
        self.logs = []

    def log_action(self, agent_name, action_type, details):
        entry = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action_type,
            "details": details
        }
        with self.lock:
            self.logs.append(entry)
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to write log: {e}")

    def get_logs(self, agent_name=None):
        with self.lock:
            if agent_name:
                return [log for log in self.logs if log["agent"] == agent_name]
            return list(self.logs)g for log in self.logs if log["agent"] == agent_name]
            return list(self.logs)ts monitoring in a separate thread, allowing main process to continue.
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