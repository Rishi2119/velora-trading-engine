# 04 - System Architecture

## Description
A highly modular micro-architecture focusing on isolation, fault tolerance, and deterministic outputs via the Agent reasoning engine.

## Core Services
1. **Agent Controller API**: Ingests commands from the mobile application.
2. **Continuous Loop**: The underlying heartbeat.
3. **Reasoning Engine**: Transforms raw state into actionable JSON outputs via NVIDIA API.
4. **Decision Engine**: Rule-based scoring applied post-LLM reasoning.
5. **Execution Layer**: Invokes trading commands via MT5 Manager.
