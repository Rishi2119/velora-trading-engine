"""
Autonomous Agent Loop — Production Edition
==========================================
24/7 continuous operation with:
  - Kill switch check on every iteration
  - Goal lifecycle management (pending → in_progress → complete)
  - Configurable confidence threshold before execution
  - Structured exception handling so the loop NEVER crashes permanently
  - Memory persistence after every successful trade
"""

import time
import json
import os
from datetime import datetime
from agent.utils.logger import logger
from agent.utils.errors import ExecutionError
from agent.modules.goal_intake import GoalIntakeModule
from agent.modules.task_decomposition import TaskDecompositionEngine
from agent.modules.sentiment import SentimentAnalyzer
from agent.core.reasoning import KimiReasoningCore
from agent.core.decision import DecisionEngine
from agent.memory.short_term import ShortTermMemory
from agent.memory.long_term import LongTermMemory
from agent.execution.executor import ExecutionLayer

# ─── Kill switch path ────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_AGENT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))   # autonomous_agent/
_REPO_ROOT = os.path.dirname(_AGENT_ROOT)                   # trading_engins/
_KILL_SWITCH = os.path.join(_REPO_ROOT, "mobile_api", "KILL_SWITCH.txt")

# Default trading goal — overridden by set_goal() or config
DEFAULT_GOAL = (
    "Monitor EURUSD and GBPUSD during active London and New York sessions. "
    "If a high-quality setup (3:1 R:R minimum) is identified, execute a small trade. "
    "Always respect the kill switch and risk limits."
)


class AutonomousLoop:
    def __init__(self, config: dict):
        self.config = config
        self.interval = config.get("agent", {}).get("loop_interval_seconds", 30)
        self.max_iterations = config.get("agent", {}).get("max_iterations", 10000)
        self.min_confidence = config.get("safety", {}).get("min_confidence_threshold", 0.65)

        # Memory layers
        self.short_term = ShortTermMemory()
        mem_path = config.get("memory", {}).get("storage_path", "data/memory.json")
        self.long_term = LongTermMemory(mem_path)

        # Core layers
        self.reasoning = KimiReasoningCore(config)
        self.decision = DecisionEngine(self.reasoning)
        self.executor = ExecutionLayer(config)

        # Modules
        self.goal_intake = GoalIntakeModule()
        self.task_decomposition = TaskDecompositionEngine(self.reasoning)
        self.sentiment_analyzer = SentimentAnalyzer()

        # State
        self.running = False
        self.iteration = 0
        self._consecutive_errors = 0
        self._max_consecutive_errors = 10  # back-off after N consecutive failures

        # Pre-load the default trading goal
        self.goal_intake.add_goal(DEFAULT_GOAL)

    # ─── External control ────────────────────────────────────────────────

    def set_goal(self, goal_description: str):
        """Add / replace the primary trading goal."""
        # Clear stale goals first
        for g in self.goal_intake.goals:
            if g["status"] == "pending":
                g["status"] = "superseded"
        self.goal_intake.add_goal(goal_description)

    def start(self):
        self.running = True
        logger.info("=" * 60)
        logger.info("  Velora Autonomous Agent — STARTED")
        logger.info(f"  Loop interval: {self.interval}s | Max iterations: {self.max_iterations}")
        logger.info("=" * 60)

        while self.running and self.iteration < self.max_iterations:
            try:
                self._run_iteration()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received — stopping agent.")
                self.stop()
                break
            except Exception as e:
                self._consecutive_errors += 1
                logger.error(f"Unhandled loop exception #{self._consecutive_errors}: {e}", exc_info=True)
                if self._consecutive_errors >= self._max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({self._consecutive_errors}). "
                        "Sleeping 5 minutes before retrying."
                    )
                    time.sleep(300)
                    self._consecutive_errors = 0
                else:
                    self._sleep()

        logger.info("Autonomous loop terminated.")

    def stop(self):
        self.running = False
        logger.info("Agent stop signal received.")

    # ─── Main iteration ──────────────────────────────────────────────────

    def _run_iteration(self):
        self.iteration += 1
        logger.info(f"--- Iteration {self.iteration} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

        # 0. Kill switch check — respect immediately
        if os.path.exists(_KILL_SWITCH):
            logger.warning("🛑 Kill switch active — skipping this iteration.")
            self._sleep()
            return

        # 1. Get current goal
        current_goal = self.goal_intake.get_next_goal()
        if not current_goal:
            # Re-inject the default trading goal so we never idle permanently
            logger.info("No active goals — re-injecting default trading goal.")
            self.goal_intake.add_goal(DEFAULT_GOAL)
            self._sleep()
            return

        # Mark it in-progress so it is not re-picked
        current_goal["status"] = "in_progress"
        logger.info(f"Goal: {current_goal['description'][:120]}")

        # 2. Gather context
        past_exp = self.long_term.retrieve_relevant_experience(current_goal["description"])
        recent_ctx = self.short_term.get_context()
        market_sentiment = self.sentiment_analyzer.get_market_sentiment()

        state_summary = (
            f"Goal: {current_goal['description']}\n"
            f"Recent Context (last actions): {json.dumps(recent_ctx[-3:], default=str)}\n"
            f"Relevant Past Experiences: {json.dumps(past_exp, default=str)}\n"
            f"Market Sentiment: {market_sentiment['label']} "
            f"(Score: {market_sentiment['score']}) — {market_sentiment['summary']}\n"
            f"Current UTC Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"Kill Switch: {'ACTIVE' if os.path.exists(_KILL_SWITCH) else 'inactive'}"
        )

        # 3. AI reasoning → decision
        recent_success = self.short_term.get_recent_success_rate()
        decision_obj = self.decision.evaluate(
            state_summary,
            recent_success_rate=recent_success
        )
        confidence = decision_obj.get("confidence_score", 0.0)

        logger.info(
            f"Decision: {decision_obj.get('decision')} | "
            f"Confidence: {confidence:.0%} | "
            f"Threshold: {self.min_confidence:.0%}"
        )

        # 4. Execute if TRADE and confidence meets threshold
        if decision_obj.get("decision") == "TRADE" and confidence >= self.min_confidence:
            next_action_str = decision_obj.get("next_action", "{}")

            try:
                action_payload = json.loads(next_action_str)
            except (json.JSONDecodeError, TypeError):
                action_payload = {"tool": "none"}

            if action_payload.get("tool") not in (None, "none", ""):
                outcome = self.executor.execute(action_payload)

                # 5. Store in short-term memory
                self.short_term.add({
                    "goal": current_goal["description"][:80],
                    "action": action_payload,
                    "outcome": outcome,
                    "timestamp": time.time()
                })

                # 6. Store successful experiences in long-term
                if outcome.get("status") == "success":
                    self.long_term.store_experience(
                        goal=current_goal["description"],
                        plan=decision_obj.get("thought_process", ""),
                        outcome=outcome
                    )
                    self._consecutive_errors = 0  # reset error counter on success

                # 7. Mark goal complete — add a fresh monitoring goal for next cycle
                current_goal["status"] = "completed"
                self.goal_intake.add_goal(DEFAULT_GOAL)
            else:
                # Tool is 'none' — still mark in-progress goal as complete so it refreshes
                current_goal["status"] = "completed"
                self.goal_intake.add_goal(DEFAULT_GOAL)
        else:
            reason = "confidence too low" if confidence < self.min_confidence else "decision was NO TRADE"
            logger.info(f"No execution ({reason}). Resetting goal for next cycle.")
            # Reset to pending so it is re-evaluated next iteration
            current_goal["status"] = "pending"

        self._sleep()

    def _sleep(self):
        time.sleep(self.interval)
