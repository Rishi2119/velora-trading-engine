# Autonomous AI Agent (Kimi K2.5 Powered)

A persistent, self-improving AI agent running a 24/7 continuous loop, complete with a structured decision engine, execution layer, and robust persistent memory.

## Architecture

```
Goal Intake -> Memory Retrieval -> Reasoning Engine -> Decision (TRADE/NO TRADE) -> Execution Layer -> Memory Storage
```

### Components
1. **Loop Layer** (`agent/core/loop.py`): The 24/7 heartbeat of the system.
2. **Reasoning Core** (`agent/core/reasoning.py`): Integrates with NVIDIA Kimi K2.5 API, outputting deterministic JSON.
3. **Decision Engine** (`agent/core/decision.py`): Evaluates state to output `TRADE`/`NO TRADE` triggers.
4. **Memory System** (`agent/memory/`): Separates session short-term memory and JSON-backed long-term persistent storage.
5. **Execution Layer** (`agent/execution/`): Executes allowed Python functions, guarded by a risk control system.
6. **Goal & Task Modules** (`agent/modules/`): Breaks down high-level goals into smaller sequential tasks.

## Setup Instructions

1. **Clone & Environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and insert your NVIDIA/Kimi API key.
   ```bash
   cp .env.example .env
   ```
   Adjust `config.yaml` to modify the loop interval, safety rules, and model settings.

3. **Running the Agent**:
   ```bash
   python main.py
   ```
   *The agent will begin its continuous loop. Use `Ctrl+C` to activate the emergency kill switch and shut down gracefully.*
