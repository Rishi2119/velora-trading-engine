# 02 - User Stories and Acceptance Criteria

## US1: Monitor Agent
**As a** user, **I want** to see the agent's thought process in the app, **so that** I understand its trading basis.
**AC**: App dynamically displays `thought_process` and `decision` variables.

## US2: Emergency Stop
**As a** user, **I want** a dedicated kill switch, **so that** I can abort operations instantly.
**AC**: Agent terminates its Python loop within 1 second of parsing the STOP command.

## US3: Autonomous Execution
**As an** agent, **I want** to continuously review market data, **so that** I don't miss opportunities.
**AC**: Agent safely runs 24/7, catching exceptions appropriately.
