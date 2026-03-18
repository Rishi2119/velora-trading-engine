# 12 - Testing Strategy

## Approach
Our goal is to test reasoning consistency without executing live trades.

## 1. Unit Tests
- Testing JSON deserialization safety in `reasoning.py`.
- Validation of the `decision.py` threshold triggers (confidence bounds).

## 2. API Mocking
Using dummy keys to trigger the failover mock response (`_mock_response`) to ensure the agent loop does not halt on API network timeouts.

## 3. Integration Testing (Dry-Run)
- Setting a `SAFE_MODE` flag that processes data and logs "would have executed TRADE" instead of actually invoking the MT5 API.

## 4. Mobile E2E
- Using Expo tooling to verify the Velora app UI updates gracefully when the Agent state switches to `NO TRADE` with varying thought processes.
