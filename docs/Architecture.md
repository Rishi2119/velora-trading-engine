# Autonomous Agent Architecture

## Overview
The Velora Autonomous Trading Agent is a persistent AI system designed for 24/7 trading using the NVIDIA Kimi K2.5 API.

## Components
- **Loop Layer**: `agent/core/loop.py` - Manages the continuous execution cycle.
- **Reasoning Core**: `agent/core/reasoning.py` - Interfaces with the LLM to process context and decide on actions.
- **Decision Engine**: `agent/core/decision.py` - Computes and outputs explicit `TRADE` or `NO TRADE` signals.
- **Memory System**: `agent/memory/` - Handles short-term context and long-term JSON-backed persistence.
- **Execution Layer**: `agent/execution/` - Safely executes allowed functions such as trades via MT5.

## Data Flow
Goal Intake -> Memory Retrieval -> Reasoning Engine -> Decision -> Execution Layer -> Memory Storage
