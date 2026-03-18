# 06 - API Contracts

The Agent exposes a local RESTful status API consumed by the Velora mobile app.

## Agent Controller API

### `GET /agent/state`
Returns the current agent status and its latest thought string.
**Response**:
```json
{
  "status": "running",
  "uptime_seconds": 3600,
  "current_thought": "Analyzing EURUSD moving averages...",
  "last_decision": "NO TRADE"
}
```

### `POST /agent/command`
Pushes control commands (Start/Stop) to the Loop layer.
**Payload**: `{"command": "STOP"}`
**Response**: `{"status": "Agent shutdown initiated."}`
