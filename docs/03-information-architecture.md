# 03 - Information Architecture

## 1. State Management
- **Short-Term Memory**: In-memory rolling buffer (e.g., maintaining the last 5 interactions).
- **Long-Term Memory**: Non-volatile JSON files (`data/memory.json`).

## 2. Structure & Logs
The system utilizes structured JSON logging for both persistence and app interaction:
```json
{
  "timestamp": "2026-03-03T10:00:00Z",
  "level": "INFO",
  "module": "ReasoningCore",
  "message": "Evaluated market state.",
  "meta": {"confidence": 0.95, "decision": "TRADE"}
}
```
