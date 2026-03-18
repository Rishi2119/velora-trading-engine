# // turbo
"""
Velora AI Engine — DeepSeek Decision Brain
All trading decisions pass through this module.
"""
import httpx
import json
import asyncio
from loguru import logger
from config.settings import config
from typing import Optional

class DeepSeekBrain:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_BASE_URL
        self.model = config.DEEPSEEK_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.system_prompt = """You are Velora, an institutional-grade AI trading engine.
You analyze forex market data with precision and discipline.
You NEVER suggest trades that violate risk rules.
You respond ONLY in valid JSON format.
You think like a senior quant analyst at a hedge fund.
Your decisions must be data-driven, not emotional.
Maximum risk per trade: 1%. Daily loss limit: 3%. Max drawdown: 10%."""

    async def _call(self, user_message: str, max_tokens: int = 1000) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)

    async def analyze_market_regime(self, market_data: dict) -> dict:
        prompt = f"""Analyze this forex market data and determine the market regime.

Market Data:
{json.dumps(market_data, indent=2)}

Respond with this exact JSON:
{{
  "regime": "trending_up|trending_down|ranging|high_volatility|low_volatility",
  "confidence": 0.0-1.0,
  "best_strategy_type": "trend_following|mean_reversion|breakout|reversal",
  "avoid_pairs": [],
  "reasoning": "2-sentence explanation",
  "session_quality": "excellent|good|poor"
}}"""
        try:
            return await self._call(prompt)
        except Exception as e:
            logger.error(f"[DeepSeek] Market regime analysis failed: {e}")
            return {"regime": "unknown", "confidence": 0.0, "best_strategy_type": "trend_following",
                    "avoid_pairs": [], "reasoning": "API unavailable", "session_quality": "poor"}

    async def select_strategy(self, regime: dict, available_strategies: list, pair: str) -> dict:
        prompt = f"""Select the optimal trading strategy for current conditions.

Current Market Regime: {json.dumps(regime)}
Trading Pair: {pair}
Available Strategies (from Velora dataset):
{json.dumps(available_strategies[:5], indent=2)}

Respond with this exact JSON:
{{
  "selected_strategy_id": "S001",
  "selected_strategy_name": "Strategy Name",
  "confidence": 0.0-1.0,
  "reasoning": "Why this strategy fits right now",
  "alternative_strategy_id": "S002",
  "skip_trading": false,
  "skip_reason": ""
}}"""
        try:
            return await self._call(prompt)
        except Exception as e:
            logger.error(f"[DeepSeek] Strategy selection failed: {e}")
            return {"selected_strategy_id": "NONE", "confidence": 0.0, "skip_trading": True,
                    "skip_reason": "AI unavailable — skipping for safety"}

    async def validate_signal(self, signal: dict, strategy: dict, account: dict) -> dict:
        prompt = f"""Validate this trading signal before execution.

Signal: {json.dumps(signal, indent=2)}
Strategy Rules: {json.dumps(strategy, indent=2)}
Account State: {json.dumps(account, indent=2)}

Check:
1. Does signal match strategy entry rules?
2. Is risk within limits (1% per trade, 3% daily, 10% total drawdown)?
3. Is R:R ratio acceptable (minimum 1.5)?
4. Is this a high-quality setup or borderline?

Respond with this exact JSON:
{{
  "approved": true|false,
  "confluence_score": 0-100,
  "risk_reward_ratio": 0.0,
  "position_size_lots": 0.0,
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit_1": 0.0,
  "take_profit_2": 0.0,
  "rejection_reason": "",
  "warnings": []
}}"""
        try:
            return await self._call(prompt, max_tokens=600)
        except Exception as e:
            logger.error(f"[DeepSeek] Signal validation failed: {e}")
            return {"approved": False, "rejection_reason": "AI validation unavailable — blocked for safety",
                    "confluence_score": 0, "warnings": ["DeepSeek API error"]}

    async def review_performance(self, trades: list, account: dict) -> dict:
        prompt = f"""Review today's trading performance and provide analysis.

Closed Trades: {json.dumps(trades, indent=2)}
Account: {json.dumps(account, indent=2)}

Respond with this exact JSON:
{{
  "total_pnl": 0.0,
  "win_rate_today": 0.0,
  "best_trade": "description",
  "worst_trade": "description",
  "pattern_observed": "what pattern in wins/losses",
  "recommendation_tomorrow": "what to adjust",
  "risk_assessment": "safe|caution|stop_trading",
  "performance_score": 0-100
}}"""
        try:
            return await self._call(prompt, max_tokens=800)
        except Exception as e:
            logger.error(f"[DeepSeek] Performance review failed: {e}")
            return {"total_pnl": 0.0, "risk_assessment": "caution", "performance_score": 0}

brain = DeepSeekBrain()
