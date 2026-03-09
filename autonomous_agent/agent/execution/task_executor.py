from agent.utils.logger import logger
from agent.utils.errors import ExecutionError
from agent.modules.sentiment import SentimentAnalyzer

class DynamicTaskExecutor:
    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.mapped_skills = {
            "analyze_sentiment": self.sentiment.get_market_sentiment
        }
    
    def execute_sub_task(self, task_description, skill_name=None, **kwargs):
        """
        Dynamically routes a sub-task to a specific mapped skill/function,
        or simulates execution if no strict skill is defined.
        """
        logger.info(f"Executing dynamic sub-task: {task_description}")
        
        if skill_name and skill_name in self.mapped_skills:
            try:
                result = self.mapped_skills[skill_name](**kwargs)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Skill execution error: {e}")
                return {"status": "error", "message": str(e)}
        else:
            # Simulated execution for generalized sub-tasks
            logger.info(f"No specific skill mapped for {skill_name}. Simulating generalized execution.")
            return {
                "status": "success", 
                "result": f"Simulated execution for task '{task_description}'."
            }
