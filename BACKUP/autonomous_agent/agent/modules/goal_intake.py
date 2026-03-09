import uuid
from agent.utils.logger import logger

class GoalIntakeModule:
    def __init__(self):
        self.goals = []
        
    def add_goal(self, goal_description):
        goal = {
            "id": uuid.uuid4().hex,
            "description": goal_description,
            "status": "pending",
            "priority": "normal"
        }
        self.goals.append(goal)
        logger.info(f"New goal accepted: {goal_description}")
        return goal["id"]
        
    def get_next_goal(self):
        for goal in self.goals:
            if goal["status"] == "pending":
                return goal
        return None
        
    def mark_completed(self, goal_id):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["status"] = "completed"
                logger.info(f"Goal completed: {goal['description']}")
                break
