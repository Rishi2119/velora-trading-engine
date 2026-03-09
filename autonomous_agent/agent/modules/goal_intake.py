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

    def generate_and_add_sub_tasks(self, decomposition_engine, parent_goal_id, context=""):
        parent_goal = None
        for g in self.goals:
            if g["id"] == parent_goal_id:
                parent_goal = g
                break
                
        if not parent_goal:
            return []
            
        logger.info(f"Dynamically generating sub-tasks for goal: {parent_goal['description']}")
        tasks = decomposition_engine.break_down_goal(parent_goal, context)
        
        sub_goal_ids = []
        for task in tasks:
            # We add sub-tasks as new high-priority goals 
            # so the loop picks them up immediately
            goal_id = uuid.uuid4().hex
            self.goals.insert(0, {
                "id": goal_id,
                "description": f"Sub-Task of {parent_goal_id}: " + task.get("description", "Unknown Action"),
                "status": "pending",
                "priority": "high"
            })
            sub_goal_ids.append(goal_id)
            logger.info(f"Added high-priority sub-task: {task.get('description')}")
            
        return sub_goal_ids

