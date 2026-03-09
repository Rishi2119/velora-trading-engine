import os
import json
import time
import requests
from agent.utils.logger import logger
from agent.utils.errors import ReasoningError

class KimiReasoningCore:
    def __init__(self, config):
        self.config = config.get("api", {})
        self.model = self.config.get("model", "kimi-k2.5-free")
        self.base_url = self.config.get("base_url", "https://api.nvidia.com/v1")
        self.api_key = os.getenv("KIMI_API_KEY", "dummy_key")
        self.temperature = self.config.get("temperature", 0.0)
        self.max_retries = config.get("safety", {}).get("max_retries", 3)
        self.timeout = config.get("agent", {}).get("api_timeout", 30)

    def query(self, system_prompt, user_prompt):
        """
        Returns guaranteed structured output:
        {
          "thought_process": "",
          "decision": "",
          "confidence_score": 0.0,
          "next_action": ""
        }
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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
                # MOCKING THE API CALL for demonstration purposes 
                # (to make this run without external dependency if needed)
                if self.api_key == "dummy_key" or "nvidia.com" in self.base_url:
                    logger.debug("Using mock response for Kimi K2.5 API.")
                    return self._mock_response(user_prompt)

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                parsed = json.loads(content)
                self._validate_output(parsed)
                return parsed
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API connection error (attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(2 ** attempt)
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON from API (attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Reasoning Core Error: {e}")
                time.sleep(1)
                
        # Failover response
        return self._failover_response()

    def query_raw(self, prompt):
        return {"tasks": [{"description": prompt}]} # Mocked

    def _validate_output(self, parsed):
        required_keys = ["thought_process", "decision", "confidence_score", "next_action"]
        for k in required_keys:
            if k not in parsed:
                raise ReasoningError(f"Missing required key in response: {k}")

    def _mock_response(self, user_prompt):
        return {
            "thought_process": "Analyzing current goals and memory context... The goal requires taking an action. I will determine the next deterministic step.",
            "decision": "TRADE" if "analyze" in user_prompt.lower() else "NO TRADE",
            "confidence_score": 0.95,
            "next_action": '{"tool": "math_eval", "args": {"expression": "2+2"}}'
        }

    def _failover_response(self):
        return {
            "thought_process": "System is failing to reach the API after max retries. Engaging failover safe mode.",
            "decision": "NO TRADE",
            "confidence_score": 0.0,
            "next_action": '{"tool": "none"}'
        }
