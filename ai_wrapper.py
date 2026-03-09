"""
AI Wrapper - Integrates ai_agents with AISandbox for safe execution
Ensures all AI outputs go through validation before any trading
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AIWrapper:
    """
    Wrapper that integrates AI agents with sandbox for safe operation.
    
    All AI outputs MUST go through validate_signal() before any trading.
    AI can NEVER execute directly.
    """
    
    def __init__(self, sandbox, risk_manager):
        self.sandbox = sandbox
        self.risk_manager = risk_manager
        self.agent = None
        
        # Initialize AI agents
        try:
            from ai_agents import AIFinanceAgentTeam
            self.agent = AIFinanceAgentTeam()
            logger.info("AI Wrapper: AIFinanceAgentTeam loaded")
        except ImportError as e:
            logger.warning(f"AI Wrapper: Could not load AIFinanceAgentTeam: {e}")
    
    def analyze_market(self, df, symbol: str) -> Dict[str, Any]:
        """
        Analyze market using AI agents.
        
        Returns raw analysis (not a trade signal).
        """
        if self.agent is None:
            return {"error": "AI agent not available", "recommendations": []}
        
        try:
            return self.agent.analyze(df, symbol)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"error": str(e), "recommendations": []}
    
    def get_signal(self, df, symbol: str, min_confidence: int = 70) -> Dict[str, Any]:
        """
        Get a trade signal from AI.
        
        This method:
        1. Runs AI analysis
        2. Extracts the top recommendation
        3. Returns signal for sandbox validation
        
        Does NOT execute - only returns signal for validation.
        """
        if self.agent is None:
            return {
                "approved": False,
                "reason": "AI agent not available",
                "signal": None
            }
        
        try:
            # Get analysis
            analysis = self.agent.analyze(df, symbol)
            
            if 'recommendations' not in analysis or not analysis['recommendations']:
                return {
                    "approved": False,
                    "reason": "No recommendations from AI",
                    "signal": None
                }
            
            # Get top recommendation
            recommendations = analysis['recommendations']
            top_rec = max(recommendations, key=lambda x: x.get('confidence', 0))
            
            # Skip WAIT signals
            if top_rec.get('action', '').upper() == 'WAIT':
                return {
                    "approved": False,
                    "reason": f"AI recommended WAIT (confidence: {top_rec.get('confidence', 0)}%)",
                    "signal": None
                }
            
            # Skip low confidence
            if top_rec.get('confidence', 0) < min_confidence:
                return {
                    "approved": False,
                    "reason": f"Confidence {top_rec.get('confidence')} below threshold {min_confidence}%",
                    "signal": None
                }
            
            # Convert to standard signal format
            signal = {
                "symbol": symbol,
                "direction": "LONG" if top_rec.get('action', '').upper() == "BUY" else "SHORT",
                "entry": top_rec.get('entry'),
                "sl": top_rec.get('stop'),
                "tp": top_rec.get('target'),
                "confidence": top_rec.get('confidence', 0),
                "reason": top_rec.get('reason', ''),
                "source": "ai_agents"
            }
            
            return {
                "approved": True,
                "reason": "Signal extracted from AI",
                "signal": signal,
                "raw_analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI signal: {e}")
            return {
                "approved": False,
                "reason": f"AI error: {str(e)}",
                "signal": None
            }
    
    def validate_through_sandbox(self, signal: Dict, balance: float) -> Dict[str, Any]:
        """
        Send AI signal through sandbox for validation.
        
        This is the REQUIRED method before any trade execution.
        """
        if signal is None:
            return {
                "approved": False,
                "reason": "No signal to validate",
                "action": "NO_TRADE"
            }
        
        try:
            return self.sandbox.request_trade(signal, balance)
        except Exception as e:
            logger.error(f"Sandbox validation failed: {e}")
            return {
                "approved": False,
                "reason": f"Sandbox error: {str(e)}",
                "action": "NO_TRADE"
            }
    
    def get_trade_decision(self, df, symbol: str, balance: float, 
                          min_confidence: int = 70) -> Dict[str, Any]:
        """
        Complete flow: AI analysis -> signal -> sandbox validation
        
        Returns final decision with all validation passed.
        """
        # Step 1: Get AI signal
        signal_result = self.get_signal(df, symbol, min_confidence)
        
        if not signal_result.get("approved"):
            return {
                "decision": "NO_TRADE",
                "reason": signal_result.get("reason", "AI signal rejected"),
                "stage": "ai_analysis"
            }
        
        # Step 2: Validate through sandbox
        validation = self.validate_through_sandbox(signal_result["signal"], balance)
        
        if not validation.get("approved"):
            return {
                "decision": "NO_TRADE",
                "reason": validation.get("reason", "Sandbox validation failed"),
                "stage": "sandbox_validation",
                "signal": signal_result["signal"]
            }
        
        # Both passed - return approved trade
        return {
            "decision": "APPROVED",
            "reason": "AI signal + sandbox validation passed",
            "stage": "ready_for_execution",
            "trade_params": validation.get("validated_params"),
            "signal": signal_result["signal"]
        }
    
    def is_available(self) -> bool:
        """Check if AI is available"""
        return self.agent is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get wrapper status"""
        return {
            "ai_available": self.is_available(),
            "sandbox_status": self.sandbox.get_status() if self.sandbox else None,
            "risk_limits": self.risk_manager.get_stats() if self.risk_manager else None
        }
