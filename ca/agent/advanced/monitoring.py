"""Minimal agent monitoring utilities."""
import json
import logging
import time
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BLUX-cA-Monitor")


class AgentMonitor:
    """Thread-safe log sink for agent actions."""

    def __init__(self, log_file: str = "blux_agent.log"):
        self.log_file = log_file
        self.lock = Lock()
        self.logs: List[Dict[str, Any]] = []

    def log_action(self, agent_name: str, action_type: str, details: Dict[str, Any]) -> None:
        entry = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action_type,
            "details": details,
        }
        with self.lock:
            self.logs.append(entry)
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as exc:
                logger.error(f"Failed to write log: {exc}")

    def get_logs(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            if agent_name:
                return [log for log in self.logs if log.get("agent") == agent_name]
            return list(self.logs)

    def start_live_monitoring(self, interval: int = 5) -> Thread:
        """Starts monitoring in a separate thread, allowing main process to continue."""

        thread = Thread(target=self.live_monitor, args=(interval,), daemon=True)
        thread.start()
        return thread

    def live_monitor(self, interval: int = 5) -> None:
        """Periodically emit log counts."""

        while True:
            with self.lock:
                logger.info("AgentMonitor heartbeat: %s entries", len(self.logs))
            time.sleep(interval)

    def stop_monitoring(self) -> None:
        logger.info("AgentMonitor stop requested (noop placeholder)")


__all__ = ["AgentMonitor"]
