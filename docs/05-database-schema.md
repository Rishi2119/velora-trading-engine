# 05 - Database Schema

Given the MVP scope, we eschew a heavy relational database in favor of a lightweight flat-file JSON document store for memory.

## Long-Term Memory File (`data/memory.json`)
```json
{
  "system_id": "AutoWorker-1",
  "sessions": [
    {
      "session_id": "uuid-v4",
      "start_time": "2026-03-03T10:00:00Z",
      "events": [
        {
          "type": "REASONING",
          "prompt": "Evaluate current EURUSD tick data.",
          "thought_process": "Indicators point downward...",
          "decision": "NO TRADE",
          "confidence_score": 0.45,
          "action_taken": "none"
        }
      ]
    }
  ]
}
```
