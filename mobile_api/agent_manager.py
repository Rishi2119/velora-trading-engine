"""
Agent Manager — Flask API Adapter for Autonomous Agent
======================================================
Controls start/stop of the autonomous agent from the mobile API.

Fixes applied:
  - No os.chdir() — manipulates sys.path properly instead
  - Loads config.yaml directly (no fragile `from main import load_config`)
  - Watchdog thread restarts the agent if it crashes silently
  - Exposes latest thought/decision/sentiment for the mobile dashboard
"""

import threading
import time
import os
import sys
import yaml
import logging

logger = logging.getLogger("agent_manager")
logging.basicConfig(level=logging.INFO)

# ─── Path setup ──────────────────────────────────────────────────────────────
# Do NOT use os.chdir() — it breaks Flask's relative file paths.
# Instead, prepend the agent directory to sys.path.

_API_DIR = os.path.dirname(os.path.abspath(__file__))   # mobile_api/
_BASE_DIR = os.path.dirname(_API_DIR)                   # trading_engins/
_AGENT_DIR = os.path.join(_BASE_DIR, "autonomous_agent")
_CONFIG_PATH = os.path.join(_AGENT_DIR, "config.yaml")

for _p in [_AGENT_DIR, _BASE_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Import agent core ───────────────────────────────────────────────────────

AutonomousLoop = None
_import_error = None

try:
    from agent.core.loop import AutonomousLoop
    logger.info("Autonomous agent core imported successfully.")
except Exception as e:
    _import_error = str(e)
    logger.error(f"Failed to import agent core: {e}")


def _load_config() -> dict:
    """Load the agent config.yaml without changing the working directory."""
    try:
        with open(_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Could not load agent config.yaml: {e}")
        return {
            "agent": {"loop_interval_seconds": 30, "max_iterations": 10000, "api_timeout": 30},
            "api": {"model": "kimi-k2.5-free", "base_url": "https://api.nvidia.com/v1", "temperature": 0.1},
            "memory": {"storage_path": os.path.join(_AGENT_DIR, "data", "memory.json")},
            "trading": {"enable_live_execution": False},
            "safety": {"allow_system_commands": False, "allow_file_deletion": False, "max_retries": 3}
        }


# ─── Agent Manager ───────────────────────────────────────────────────────────

class AgentManager:
    """
    Manages the lifecycle of the autonomous agent in a background thread.
    Includes a watchdog that restarts the agent if it exits unexpectedly.
    """

    WATCHDOG_INTERVAL = 15  # seconds between watchdog checks

    def __init__(self):
        self.agent = None
        self._agent_thread = None
        self._watchdog_thread = None
        self.running = False
        self._stop_requested = False

        self.latest_status = {
            "thought_process": "Agent is idle. Start via the Dashboard.",
            "decision": "NONE",
            "confidence_score": 0.0,
            "next_action": "none"
        }
        self.latest_sentiment = None
        self._crash_count = 0
        self._last_start_time = None

    # ─── Start ───────────────────────────────────────────────────────────

    def start(self) -> bool:
        if self.running:
            logger.info("Agent is already running.")
            return True

        if AutonomousLoop is None:
            logger.error(f"Cannot start: agent import failed — {_import_error}")
            return False

        self._stop_requested = False
        self._launch_agent()

        # Start watchdog
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop, daemon=True, name="AgentWatchdog"
        )
        self._watchdog_thread.start()
        return True

    def _launch_agent(self):
        """Create and start the agent in a background thread."""
        config = _load_config()

        # Resolve memory path relative to agent dir
        mem_path = config.get("memory", {}).get("storage_path", "data/memory.json")
        if not os.path.isabs(mem_path):
            mem_path = os.path.join(_AGENT_DIR, mem_path)
        config.setdefault("memory", {})["storage_path"] = mem_path

        self.agent = AutonomousLoop(config)

        # Intercept decision engine to capture status for the mobile dashboard
        original_evaluate = self.agent.decision.evaluate

        def intercepted_evaluate(state_summary, *args, **kwargs):
            result = original_evaluate(state_summary, *args, **kwargs)
            self.latest_status = result
            # Also capture latest sentiment from the loop
            try:
                self.latest_sentiment = self.agent.sentiment_analyzer.get_market_sentiment()
            except Exception:
                pass
            return result

        self.agent.decision.evaluate = intercepted_evaluate

        self.running = True
        self._last_start_time = time.time()
        self._agent_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="AgentLoop"
        )
        self._agent_thread.start()
        logger.info("Autonomous agent thread started.")

    def _run_loop(self):
        try:
            self.agent.start()
        except Exception as e:
            logger.error(f"Agent loop exited with exception: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Agent loop thread exited.")

    # ─── Watchdog ────────────────────────────────────────────────────────

    def _watchdog_loop(self):
        """Restart the agent if it crashes unexpectedly."""
        while not self._stop_requested:
            time.sleep(self.WATCHDOG_INTERVAL)

            if self._stop_requested:
                break

            if not self.running and not self._stop_requested:
                # Agent thread died — restart it
                self._crash_count += 1
                wait = min(60 * self._crash_count, 300)  # exponential back-off, max 5 min
                logger.warning(
                    f"Agent crashed (crash #{self._crash_count}). "
                    f"Restarting in {wait}s..."
                )
                time.sleep(wait)

                if not self._stop_requested:
                    try:
                        self._launch_agent()
                        logger.info(f"Agent restarted after crash #{self._crash_count}.")
                    except Exception as e:
                        logger.error(f"Failed to restart agent: {e}")
            else:
                # Agent still running — reset crash counter
                if self._crash_count > 0:
                    self._crash_count = 0

    # ─── Stop ────────────────────────────────────────────────────────────

    def stop(self) -> bool:
        if not self.running and self.agent is None:
            return False

        logger.info("Stopping autonomous agent...")
        self._stop_requested = True

        if self.agent:
            self.agent.stop()

        # Wait for thread to exit
        if self._agent_thread and self._agent_thread.is_alive():
            self._agent_thread.join(timeout=5)

        self.running = False
        self.latest_status = {
            "thought_process": "Agent stopped by user.",
            "decision": "NONE",
            "confidence_score": 0.0,
            "next_action": "none"
        }
        logger.info("Agent stopped.")
        return True

    # ─── Status ──────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        uptime = None
        if self.running and self._last_start_time:
            uptime = int(time.time() - self._last_start_time)

        return {
            "is_running": self.running,
            "latest_thought": self.latest_status.get("thought_process", ""),
            "latest_decision": self.latest_status.get("decision", "NONE"),
            "confidence": self.latest_status.get("confidence_score", 0.0),
            "sentiment": self.latest_sentiment,
            "crash_count": self._crash_count,
            "uptime_seconds": uptime,
            "import_error": _import_error,
        }


# Singleton
agent_manager = AgentManager()
