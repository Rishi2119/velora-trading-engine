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
        
    def clear(self):
        self.memory = []
