from agent.utils.logger import logger

class DecisionEngine:
    def __init__(self, reasoning_engine):
        self.reasoning = reasoning_engine
        
    def evaluate(self, state_summary):
        """
        Uses reasoning engine to yield a deterministic TRADE / NO TRADE decision
        """
        system_prompt = """
        You are the Decision Engine of an autonomous agent.
        You must evaluate the current state and decide whether to proceed with an action (TRADE) or wait/skip (NO TRADE).
        Also provide your confidence score (0.0 to 1.0), thought process, and a JSON payload for the next action.
        Output MUST be in strictly validated JSON matching:
        {
          "thought_process": "...",
          "decision": "TRADE or NO TRADE",
          "confidence_score": 0.9,
          "next_action": "escaped json string of tool action, or none"
        }
        """
        
        user_prompt = f"Current State:\n{state_summary}\n\nMake a decision."
        
        result = self.reasoning.query(system_prompt, user_prompt)
        logger.info(f"Decision: {result['decision']} (Confidence: {result['confidence_score']})")
        return result
