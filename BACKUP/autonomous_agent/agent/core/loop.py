import time
import json
from datetime import datetime
from agent.utils.logger import logger
from agent.utils.errors import ExecutionError
from agent.modules.goal_intake import GoalIntakeModule
from agent.modules.task_decomposition import TaskDecompositionEngine
from agent.core.reasoning import KimiReasoningCore
from agent.core.decision import DecisionEngine
from agent.memory.short_term import ShortTermMemory
from agent.memory.long_term import LongTermMemory
from agent.execution.executor import ExecutionLayer

class AutonomousLoop:
    def __init__(self, config):
        self.config = config
        self.interval = config.get("agent", {}).get("loop_interval_seconds", 5)
        self.max_iterations = config.get("agent", {}).get("max_iterations", 1000)
        
        # Initialize Memory
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(config.get("memory", {}).get("storage_path", "data/memory.json"))
        
        # Initialize Core Layers
        self.reasoning = KimiReasoningCore(config)
        self.decision = DecisionEngine(self.reasoning)
        self.executor = ExecutionLayer(config)
        
        # Initialize Modules
        self.goal_intake = GoalIntakeModule()
        self.task_decomposition = TaskDecompositionEngine(self.reasoning)
        
        self.running = False
        self.iteration = 0
        
    def set_goal(self, goal_description):
        self.goal_intake.add_goal(goal_description)
        
    def start(self):
        self.running = True
        logger.info("Initializing Autonomous Loop (24/7 Agent)...")
        
        while self.running and self.iteration < self.max_iterations:
            try:
                self.iteration += 1
                logger.info(f"--- Loop Iteration {self.iteration} ---")
                
                # 1. Check for new goals
                current_goal = self.goal_intake.get_next_goal()
                if not current_goal:
                    logger.debug("No active goals. Sleeping.")
                    self._sleep()
                    continue
                    
                # 2. Analyze current state / Fetch relevant memory
                past_experiences = self.long_term.retrieve_relevant_experience(current_goal['description'])
                recent_context = self.short_term.get_context()
                
                state_summary = f"""
                Goal: {current_goal['description']}
                Recent Context: {recent_context}
                Relevant Past Experiences: {past_experiences}
                """
                
                # 3. Plan next action / Make decision
                decision_obj = self.decision.evaluate(state_summary)
                
                # 4. Execute action
                if decision_obj['decision'] == 'TRADE' and decision_obj['confidence_score'] > 0.6:
                    next_action_str = decision_obj.get('next_action', '{}')
                    
                    try:
                        action_payload = json.loads(next_action_str)
                    except:
                        action_payload = {"tool": "none"}
                        
                    if action_payload.get("tool") != "none":
                        outcome = self.executor.execute(action_payload)
                        
                        # 5. Evaluate outcome & 6. Store memory
                        self.short_term.add({
                            "action": action_payload,
                            "outcome": outcome,
                            "timestamp": time.time()
                        })
                        
                        # Store in long term if important
                        if outcome['status'] == 'success':
                            self.long_term.store_experience(
                                goal=current_goal['description'],
                                plan=decision_obj['thought_process'],
                                outcome=outcome
                            )
                else:
                    logger.info("Decision was NO TRADE or confidence too low. Skipping execution.")
                    
                # 7. Adjust strategy (Self-Improvement Layer hooks here)
                # In a real system, we analyze failures to refine system prompts.
                
                # 8. Sleep (controlled interval)
                self._sleep()
                
            except KeyboardInterrupt:
                logger.info("Kill switch activated via KeyboardInterrupt.")
                self.stop()
            except Exception as e:
                logger.error(f"Loop error: {e}", exc_info=True)
                self._sleep()
                
        logger.info("Autonomous loop terminated.")

    def stop(self):
        self.running = False
        
    def _sleep(self):
        time.sleep(self.interval)
