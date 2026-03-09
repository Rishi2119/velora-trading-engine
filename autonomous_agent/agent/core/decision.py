from agent.utils.logger import logger

class DecisionEngine:
    def __init__(self, reasoning_engine):
        self.reasoning = reasoning_engine
        
    def evaluate(self, state_summary, **kwargs):
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
        
        # --- Memory Feedback Loop ---
        # If the agent has a high recent failure rate, we artificially 
        # lower its confidence so the executor demands higher certainty.
        recent_success_rate = kwargs.get("recent_success_rate", None)
        if recent_success_rate is not None:
            if recent_success_rate < 0.3:
                # Poor recent performance -> penalize confidence
                original_conf = result.get('confidence_score', 0)
                result['confidence_score'] = max(0.0, original_conf - 0.2)
                logger.warning(f"Confidence penalized due to recent poor performance (-0.2). Current score: {result['confidence_score']}")
            elif recent_success_rate > 0.8:
                # Strong recent performance -> boost confidence slightly
                original_conf = result.get('confidence_score', 0)
                result['confidence_score'] = min(1.0, original_conf + 0.1)
                logger.info(f"Confidence boosted due to high recent success (+0.1). Current score: {result['confidence_score']}")
                
        logger.info(f"Decision: {result['decision']} (Confidence: {result['confidence_score']})")
        return result
