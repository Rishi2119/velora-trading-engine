# core/strategy.py
import asyncio
from typing import Dict, Any
from loguru import logger
from core.deepseek_engine import deepseek_decision

class InstitutionalStrategy:
    """
    Combines institutional technical filters with an AI decision layer.
    """
    
    def __init__(self, confidence_threshold: int = 70):
        self.threshold = confidence_threshold

    def _apply_technical_filters(self, market_data: Dict[str, Any]) -> bool:
        """
        Hardcoded institutional trend and volatility filters.
        EMA 20/50/200 and RSI 35-65 boundaries.
        """
        try:
            ema_20 = market_data.get("ema_20", 0)
            ema_50 = market_data.get("ema_50", 0)
            ema_200 = market_data.get("ema_200", 0)
            rsi = market_data.get("rsi", 50)
            
            # Simple Trend Alignment check
            trend_up = (ema_20 > ema_50) and (ema_50 > ema_200)
            trend_down = (ema_20 < ema_50) and (ema_50 < ema_200)
            
            # Only trade RSI extremes (30/70) if combined with trend logic
            rsi_neutral = 35 <= rsi <= 65
            
            if (trend_up or trend_down) and rsi_neutral:
                logger.info(f"[Strategy] Technical filters passed. RSI: {rsi}")
                return True
            
            logger.debug(f"[Strategy] Filters rejected. Trend_Up: {trend_up}, Trend_Down: {trend_down}, RSI: {rsi}")
            return False
        except Exception as e:
            logger.error(f"[Strategy] Filter error: {e}")
            return False

    async def execute(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main strategy execution pipeline.
        Filters -> AI Decision -> Confidence Check.
        """
        # Step 1: Technical Qualification
        if not self._apply_technical_filters(market_data):
            return {
                "decision": "NO_TRADE",
                "direction": "NONE",
                "confidence": 0,
                "reason": "TECH_FILTER_REJECTED"
            }
        
        # Step 2: DeepSeek Decision
        ai_result = await deepseek_decision(market_data)
        
        # Step 3: Threshold Validation
        if ai_result.get("decision") == "TRADE" and ai_result.get("confidence", 0) >= self.threshold:
            logger.success(f"[Strategy] AI APPROVED TRADE: {ai_result['direction']} | Confidence: {ai_result['confidence']}")
            return ai_result
        
        # Step 4: Fallback
        logger.info(f"[Strategy] AI REJECTED TRADE or confidence too low: {ai_result.get('confidence')}")
        return {
            "decision": "NO_TRADE",
            "direction": "NONE",
            "confidence": ai_result.get("confidence", 0),
            "reason": f"AI_UNCERTAIN: {ai_result.get('reason')}"
        }

# Singleton instance
strategy_layer = InstitutionalStrategy(confidence_threshold=70)
