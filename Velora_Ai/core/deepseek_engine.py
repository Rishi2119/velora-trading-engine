# core/deepseek_engine.py
import os
import json
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("DEEPSEEK_API_KEY") # User provided this key previously
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-reasoner"

async def deepseek_decision(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes market data via DeepSeek and returns a deterministic TRADE/NO_TRADE decision.
    """
    if not OPENROUTER_API_KEY:
        logger.error("[DeepSeek Engine] OPENROUTER_API_KEY missing from environment.")
        return {"decision": "NO_TRADE", "direction": "NONE", "confidence": 0, "reason": "API_KEY_MISSING"}

    prompt = f"""
    Act as an institutional FX trader. Analyze the following market technicals and determine if a high-probability trade exists.
    
    Market Data:
    {json.dumps(market_data, indent=2)}
    
    Rules:
    1. Decision must be TRADE or NO_TRADE.
    2. Direction must be BUY, SELL, or NONE.
    3. Confidence must be a number from 0 to 100.
    4. Provide a precise reason (max 15 words).
    
    Return STRICT JSON format ONLY:
    {{
        "decision": "TRADE or NO_TRADE",
        "direction": "BUY or SELL or NONE",
        "confidence": number,
        "reason": "text"
    }}
    """

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a deterministic financial analyst. You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Cleanly parse JSON
            decision_data = json.loads(content)
            
            # Validation
            required_keys = ["decision", "direction", "confidence", "reason"]
            if all(key in decision_data for key in required_keys):
                logger.info(f"[DeepSeek Engine] Decision: {decision_data['decision']} | Confidence: {decision_data['confidence']} | {decision_data['reason']}")
                return decision_data
            
            logger.warning("[DeepSeek Engine] AI returned malformed JSON structure.")
            return {"decision": "NO_TRADE", "direction": "NONE", "confidence": 0, "reason": "MALFORMED_OUTPUT"}

    except Exception as e:
        logger.error(f"[DeepSeek Engine] API Error: {str(e)}")
        return {"decision": "NO_TRADE", "direction": "NONE", "confidence": 0, "reason": f"ERROR_{type(e).__name__}"}
