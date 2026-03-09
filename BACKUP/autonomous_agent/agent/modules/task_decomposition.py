from agent.utils.logger import logger

class TaskDecompositionEngine:
    def __init__(self, reasoning_engine):
        self.reasoning = reasoning_engine
        
    def break_down_goal(self, goal, context=""):
        logger.info(f"Decomposing goal into tasks: {goal['description']}")
        
        prompt = f"""
        Break down the following goal into executable steps.
        Goal: {goal['description']}
        Context: {context}
        
        Provide the output in JSON array under the key "tasks".
        """
        
        try:
            # Bypass strict structured generic handler and use raw API response if supported
            response = self.reasoning.query_raw(prompt)
            if "tasks" in response:
                return response["tasks"]
            return [{"description": "Execute goal directly: " + goal["description"]}]
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            return [{"description": goal["description"]}]
