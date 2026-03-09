# System Design

## Architecture
1. **Mobile Client (Velora)**: React Native app acting as the user interface for monitoring.
2. **Agent Worker**: Python loop backend operating autonomously.
3. **External Systems**: MetaTrader 5 (MT5) and NVIDIA Kimi API.

## Component Interaction
The Agent retrieves market data, uses Kimi API to reason about it, pushes viable trades via MT5, and exposes a state endpoint for the Velora app to fetch real-time thoughts.
