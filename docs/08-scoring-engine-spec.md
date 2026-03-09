# 08 - Scoring Engine Spec

## Objective
The Decision Engine acts as the definitive firewall to interpret the LLM's `confidence_score` and `decision` variables.

## Logic Flow
1. Check Agent Mode: If Stop signal is active, emit NO TRADE.
2. Read LLM output: `{"decision": "TRADE", "confidence_score": 0.95}`
3. Threshold rules:
   - If `decision` is "TRADE" AND `confidence_score` >= 0.85 -> Signal Execution Layer.
   - If `decision` is "TRADE" AND `confidence_score` < 0.85 -> Discard instruction, append to memory as "Rejected due to low confidence".
4. Execute via `mt5_manager.py` ensuring capital limits are upheld.
