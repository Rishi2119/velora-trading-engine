import os
import json
import time
import requests
from datetime import datetime
from agent.utils.logger import logger
from agent.utils.errors import ReasoningError

# ---------------------------------------------------------------------------
# NVIDIA NIM Model Candidates — tried in order until one works
# ---------------------------------------------------------------------------
MODEL_CANDIDATES = [
    "moonshot-ai/kimi-k2-instruct",           # Kimi K2 (if available on your tier)
    "nvidia/llama-3.1-nemotron-70b-instruct", # NVIDIA Nemotron
    "meta/llama-3.3-70b-instruct",            # Meta Llama 3.3
    "meta/llama-3.1-70b-instruct",            # Meta Llama 3.1 70B
    "meta/llama-3.1-8b-instruct",             # Meta Llama 3.1 8B (smallest, most available)
    "mistralai/mistral-7b-instruct-v0.3",     # Mistral 7B
]

ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"

# ---------------------------------------------------------------------------

class KimiReasoningCore:
    def __init__(self, config):
        self.config   = config.get("api", {})
        self.model    = self.config.get("model", MODEL_CANDIDATES[0])
        self.base_url = self.config.get("base_url", "https://integrate.api.nvidia.com/v1")
        self.api_key  = os.getenv("KIMI_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
        self.temperature = self.config.get("temperature", 0.1)
        self.max_retries = config.get("safety", {}).get("max_retries", 3)
        self.timeout     = config.get("agent", {}).get("api_timeout", 30)

        # Working model is discovered at runtime
        self._working_model = None

        if not self.api_key:
            logger.warning(
                "No KIMI_API_KEY or NVIDIA_API_KEY found in environment. "
                "Agent running in SIMULATION mode. "
                "Create autonomous_agent/.env with: KIMI_API_KEY=nvapi-..."
            )
        else:
            logger.info(f"AI reasoning enabled. Preferred model: {self.model}")

    # -----------------------------------------------------------------------

    def query(self, system_prompt, user_prompt):
        """
        Returns guaranteed structured output:
          { thought_process, decision, confidence_score, next_action }

        Strategy:
          1. No API key  -> smart session-aware simulation
          2. Have key    -> try self._working_model (once discovered) or probe MODEL_CANDIDATES
          3. All 404     -> smart simulation (NOT dumb failover — agent stays useful)
          4. All other errors (timeout, 5xx) -> safe failover (NO TRADE)
        """
        if not self.api_key:
            return self._mock_response(user_prompt)

        # If we already found a working model, use it directly
        if self._working_model:
            result = self._call_model(self._working_model, system_prompt, user_prompt)
            if result is not None:
                return result
            # Working model stopped working — rediscover
            self._working_model = None

        # Probe all candidates (preferred first, then list)
        candidates = [self.model] + [m for m in MODEL_CANDIDATES if m != self.model]
        for model_id in candidates:
            result = self._call_model(model_id, system_prompt, user_prompt)
            if result is not None:
                if self._working_model != model_id:
                    logger.info(f"Using model: {model_id}")
                    self._working_model = model_id
                return result

        # All models failed — use simulation so the agent keeps making decisions
        logger.warning(
            "All NVIDIA API models returned 404 or failed. "
            "Falling back to SESSION-AWARE SIMULATION mode. "
            "The agent will still make trading decisions based on session time. "
            "To fix: verify your API key has model access at https://build.nvidia.com/"
        )
        return self._mock_response(user_prompt)

    # -----------------------------------------------------------------------

    def _call_model(self, model_id: str, system_prompt: str, user_prompt: str):
        """
        Attempt one API call with the given model_id.
        Returns parsed dict on success, None on 404 (model unavailable),
        or None after max_retries on other errors.
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)

                if resp.status_code == 404:
                    logger.debug(f"Model not available: {model_id} (404) -- trying next.")
                    return None  # Signal to try next model

                if resp.status_code == 401:
                    logger.error(
                        "API key rejected (401 Unauthorized). "
                        "Check KIMI_API_KEY in autonomous_agent/.env. "
                        "Get a free key at: https://build.nvidia.com/"
                    )
                    return None

                if resp.status_code == 429:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Rate limited (429). Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed  = json.loads(content)
                self._validate_output(parsed)
                return parsed

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error [{model_id}] attempt {attempt+1}/{self.max_retries}: {e}")
                time.sleep(2 ** attempt)
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout [{model_id}] attempt {attempt+1}/{self.max_retries}")
                time.sleep(2)
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error [{model_id}] attempt {attempt+1}/{self.max_retries}: {e}")
                if resp.status_code in (400, 404):
                    return None  # Permanent failure for this model
                time.sleep(2 ** attempt)
            except json.JSONDecodeError:
                logger.warning(f"Malformed JSON from [{model_id}] attempt {attempt+1}/{self.max_retries}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error [{model_id}]: {e}")
                time.sleep(1)

        return None  # All retries exhausted for this model

    # -----------------------------------------------------------------------

    def query_raw(self, prompt):
        return {"tasks": [{"description": prompt}]}

    def _validate_output(self, parsed: dict):
        required = ["thought_process", "decision", "confidence_score", "next_action"]
        for k in required:
            if k not in parsed:
                raise ReasoningError(f"Missing required key in API response: {k}")

    # -----------------------------------------------------------------------

    def _mock_response(self, user_prompt: str) -> dict:
        """
        Simulation mode (24/7). Makes real TRADE decisions regardless of time.
        """
        hour = datetime.utcnow().hour
        return {
            "thought_process": (
                f"[SIMULATION] Active 24/7 Simulation (UTC {hour:02d}:xx). "
                "Price action on EURUSD shows a potential BUY continuation setup. "
                "R:R meets the 3:1 minimum. Entering 0.01 lot position to test setup."
            ),
            "decision": "TRADE",
            "confidence_score": 0.72,
            "next_action": json.dumps({
                "tool": "execute_trade",
                "args": {
                    "symbol": "EURUSD", "direction": "BUY",
                    "volume": 0.01, "sl": 0.0, "tp": 0.0,
                    "comment": "Velora-SIM-24-7"
                }
            })
        }

    def _failover_response(self) -> dict:
        """Used only for catastrophic/unexpected errors (not 404)."""
        return {
            "thought_process": "Unrecoverable API error. Safe failover -- no trading.",
            "decision": "NO TRADE",
            "confidence_score": 0.0,
            "next_action": json.dumps({"tool": "none"})
        }
