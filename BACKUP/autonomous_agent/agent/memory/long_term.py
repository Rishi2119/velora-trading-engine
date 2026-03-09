import json
import os
import time
from agent.utils.logger import logger

class LongTermMemory:
    def __init__(self, db_path="data/memory.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._load()
        
    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load long-term memory: {e}")
                self.data = {"experiences": [], "knowledge_graph": {}}
        else:
            self.data = {"experiences": [], "knowledge_graph": {}}
            self._save()
            
    def _save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
            
    def store_experience(self, goal, plan, outcome):
        experience = {
            "goal": goal,
            "plan": plan,
            "outcome": outcome,
            "timestamp": time.time()
        }
        self.data["experiences"].append(experience)
        self._save()
        logger.debug("Stored experience in long-term memory.")
        
    def retrieve_relevant_experience(self, current_goal):
        # Basic keyword match implementation for contextual retrieval
        relevant = []
        words = set(current_goal.lower().split())
        for exp in self.data["experiences"]:
            exp_words = set(exp["goal"].lower().split())
            if words.intersection(exp_words):
                relevant.append(exp)
        return relevant[-5:] # Return top 5 most recent relevant experiences
