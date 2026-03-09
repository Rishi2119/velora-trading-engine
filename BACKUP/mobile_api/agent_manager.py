import threading
import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_DIR = os.path.join(BASE_DIR, "autonomous_agent")
sys.path.insert(0, AGENT_DIR)

try:
    from agent.core.loop import AutonomousLoop
    from main import load_config
except ImportError as e:
    print(f"[AgentManager] Failed to import agent core: {e}")
    AutonomousLoop = None

class AgentManager:
    def __init__(self):
        self.agent = None
        self.thread = None
        self.running = False
        # To store latest agent thoughts for the mobile app
        self.latest_status = {
            "thought_process": "Agent is idle.",
            "decision": "NONE",
            "confidence_score": 0.0,
            "next_action": "none"
        }
        
    def start(self):
        if self.running or not AutonomousLoop:
            return False
            
        print("[AgentManager] Starting autonomous AI loop...")
        os.chdir(AGENT_DIR) # Agent relies on local data/ paths
        config = load_config()
        self.agent = AutonomousLoop(config)
        self.agent.set_goal("Monitor EURUSD and GBPUSD. If you see a strong setup based on your parameters, execute a TRADE.")
        
        # Override decision evaluation to intercept the output for the mobile app
        original_evaluate = self.agent.decision.evaluate
        def intercept_evaluate(state_summary):
            res = original_evaluate(state_summary)
            self.latest_status = res
            return res
        self.agent.decision.evaluate = intercept_evaluate
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        return True
        
    def _run_loop(self):
        try:
            self.agent.start()
        except Exception as e:
            print(f"[AgentManager] Loop crashed: {e}")
        finally:
            self.running = False
            
    def stop(self):
        if not self.running or not self.agent:
            return False
        print("[AgentManager] Stopping autonomous AI loop...")
        self.agent.stop()
        self.running = False
        self.latest_status = {
            "thought_process": "Agent stopped by user.",
            "decision": "NONE",
            "confidence_score": 0.0,
            "next_action": "none"
        }
        if self.thread:
            self.thread.join(timeout=2)
        return True
        
    def get_status(self):
        return {
            "is_running": self.running,
            "latest_thought": self.latest_status.get("thought_process", ""),
            "latest_decision": self.latest_status.get("decision", ""),
            "confidence": self.latest_status.get("confidence_score", 0.0)
        }

# Global singleton
agent_manager = AgentManager()
