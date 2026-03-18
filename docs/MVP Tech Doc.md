# MVP Technical Documentation

## Executive Summary
Technical specifications for the Autonomous Trading Agent MVP.

## Tech Stack
- **Language**: Python 3.x
- **AI Model**: NVIDIA Kimi K2.5 API
- **Execution**: MetaTrader 5 (MT5) via `mt5_manager.py`
- **Mobile Integration**: Velora Mobile App (React Native)

## MVP Scope
- 24/7 continuous loop backend process.
- Persistent JSON memory for historical interactions.
- Structured JSON outputs from LLM (thought_process, decision, etc.).
- Local fail-safes and emergency kill switch.
