from agent.utils.errors import MemoryOverflowError

class ShortTermMemory:
    def __init__(self, max_items=100):
        self.memory = []
        self.max_items = max_items
        
    def add(self, item):
        self.memory.append(item)
        if len(self.memory) > self.max_items:
            self.memory.pop(0) # FIFO
            
    def get_context(self, limit=10):
        return self.memory[-limit:]
        
    def get_recent_success_rate(self, limit=10):
        """
        Calculates the success rate of the last `limit` executed actions.
        Returns a float between 0.0 and 1.0, or None if no recent actions.
        """
        recent = self.memory[-limit:]
        if not recent:
            return None
            
        successes = sum(
            1 for item in recent 
            if isinstance(item.get("outcome"), dict) and item["outcome"].get("status") == "success"
        )
        return successes / len(recent)
        
    def clear(self):
        self.memory = []
