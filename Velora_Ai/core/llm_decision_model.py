import os
import sys
import json
import httpx
import logging
from typing import Dict, Any

# Ensure we can find the project root and Velora_Ai root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
root_dir = os.path.abspath(os.path.join(parent_dir, ".."))

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)

from backend.config.settings import settings
from utils.logger import get_logger


log = get_logger("LLMDecisionModel")

class LLMDecisionModel:
    """
    Decision model that uses OpenRouter (DeepSeek) to decide on trade actions.
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self._ready = bool(self.api_key)

    @property
    def is_ready(self) -> bool:
        return self._ready

    def load(self):
        """No loading required for remote model."""
        pass

    def predict(self, features, state=None) -> Dict[str, Any]:
        """
        Uses an LLM via OpenRouter to predict action: BUY, SELL, or NO_TRADE.
        """
        if not self._ready:
            return {"action": "NO_TRADE", "confidence": 0.0}

        try:
            prompt = self._build_prompt(features, state)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": (
                            "You are a professional forex trading assistant. "
                            "Analyze market data and decide on the best action. "
                            "You must respond with a JSON object."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }

            with httpx.Client(timeout=15.0) as client:
                res = client.post(self.api_url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)
                
                # Normalize result
                action = str(result.get("action", "NO_TRADE")).upper()
                confidence = float(result.get("confidence", 0.0))
                
                if action not in ["BUY", "SELL", "NO_TRADE"]:
                    action = "NO_TRADE"

                return {"action": action, "confidence": round(confidence, 4)}

        except Exception as e:
            log.error(f"LLM Prediction failed: {e}")
            return {"action": "NO_TRADE", "confidence": 0.0}

    def _build_prompt(self, features, state=None) -> str:
        """Constructs a prompt with market features + state for the LLM."""
        f = features
        s = state
        
        prompt = f"""
Analyze the following market conditions and determine if a trade should be opened.
Respond with a JSON object: {{"action": "BUY"|"SELL"|"NO_TRADE", "confidence": 0.0-1.0, "reason": "concise reasoning"}}

Context:
- Symbol: {s.symbol if s else 'Unknown'}
- Session: {f.session}
- Strategy: {f.strategy_type}
- Volatility: {f.volatility:.2f}

Technical Features (Normalized 0.0 to 1.0):
- Momentum: {f.momentum_strength:.2f}
- Structure Break (BOS): {f.structure_break}
- Liquidity Sweep: {f.liquidity_sweep}
- Pullback Active: {f.pullback}
- Supply/Demand Strength: {f.support_resistance_strength:.2f}

Raw Price Data:
"""
        if s:
            prompt += f"""- Open: {s.open} | High: {s.high} | Low: {s.low} | Close: {s.close}
- EMA Fast (50): {s.ema_fast} | EMA Slow (200): {s.ema_slow}
- RSI (14): {s.rsi:.2f}
- ATR: {s.atr}
- Current Spread: {s.spread}
"""
        else:
            prompt += "- Raw state missing.\n"
            
        prompt += "\nDecision: Provide action and confidence."
        return prompt

