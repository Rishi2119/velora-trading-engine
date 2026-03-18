# // turbo
"""
Velora AI Engine — Main Orchestrator
Coordinates all layers: market data -> AI analysis -> signal -> validation -> execution.
This is the brain stem. One loop runs everything.
"""
import asyncio
import json
from datetime import datetime, timezone
from loguru import logger
from config.settings import config
from core.mt5_connector import connector
from core.technical_engine import tech_engine
from core.risk_manager import risk_manager
from core.signal_generator import signal_generator
from ai.deepseek_brain import brain
from ai.strategy_loader import strategy_loader
from utils.supabase_logger import db_logger
from typing import Optional


class TradingEngine:
    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.last_regime = {}

    async def startup(self) -> bool:
        logger.info("[Velora] Starting up...")
        if not connector.connect():
            logger.error("[Velora] MT5 connection failed — cannot start")
            return False
        account = connector.get_account()
        logger.success(f"[Velora] Balance: {account.get('balance', 0):.2f} {account.get('currency', '')}")
        await db_logger.log_event("system", "startup", {"account": account})
        return True

    async def _analyze_pair(self, symbol: str, regime: dict):
        try:
            df = connector.get_ohlcv(symbol, config.TIMEFRAMES["H4"], bars=200)
            if df is None:
                return

            account = connector.get_account()
            open_positions = connector.get_open_positions()

            risk_check = risk_manager.check_trade_allowed(account, open_positions)
            if not risk_check["allowed"]:
                logger.warning(f"[Risk] {symbol} blocked: {risk_check['reason']}")
                return

            if risk_manager.is_news_blackout():
                logger.info(f"[Risk] News blackout — skipping {symbol}")
                return

            # Already have a trade on this pair?
            existing = [p for p in open_positions if p["symbol"] == symbol]
            if existing:
                return

            # Get best strategies for current regime
            session = signal_generator._get_session()
            strategies = strategy_loader.get_strategies_for_regime(regime.get("regime", "trending_up"), session)

            # Ask DeepSeek to pick the best strategy
            ds_pick = await brain.select_strategy(regime, strategies, symbol)
            if ds_pick.get("skip_trading"):
                logger.info(f"[DeepSeek] Skipping {symbol}: {ds_pick.get('skip_reason')}")
                return

            strategy = strategy_loader.get_strategy_by_id(ds_pick.get("selected_strategy_id", ""))
            if not strategy:
                strategy = strategies[0] if strategies else {}
            if not strategy:
                return

            # Generate technical signal
            raw_signal = signal_generator.generate(symbol, df, strategy)
            if not raw_signal.get("valid"):
                logger.debug(f"[Signal] {symbol} — no valid signal: {raw_signal.get('reason','')}")
                return

            # Calculate SL/TP
            info = connector.get_symbol_info(symbol)
            digits = info.get("digits", 5)
            atr = raw_signal.get("atr", 0.001)
            direction = raw_signal["direction"]
            entry = info.get("ask") if direction == "BUY" else info.get("bid")
            if not entry:
                return

            sl_tp = risk_manager.calculate_sl_tp(entry, direction, atr, digits, rr=strategy.get("avg_rr", 2.0))

            # Position sizing
            pip_value = 10.0  # approximate for majors; extend for crosses
            lots = risk_manager.calculate_position_size(
                account.get("balance", 1000),
                sl_tp["sl_pips"],
                pip_value,
                symbol
            )

            # DeepSeek final validation
            signal_payload = {
                "symbol": symbol, "direction": direction, "entry": entry,
                "sl": sl_tp["sl"], "tp": sl_tp["tp2"], "lots": lots,
                "confluence_score": raw_signal["confluence"],
                "strategy": strategy.get("name"), "session": session
            }
            account_payload = {
                "balance": account.get("balance"), "equity": account.get("equity"),
                "open_trades": len(open_positions), "daily_pnl": risk_manager.get_daily_pnl()
            }

            validation = await brain.validate_signal(signal_payload, strategy, account_payload)

            if not validation.get("approved"):
                logger.info(f"[DeepSeek] Signal rejected for {symbol}: {validation.get('rejection_reason')}")
                await db_logger.log_signal_rejected(symbol, direction, validation)
                return

            # FINAL CONFLUENCE CHECK — must be >= 60
            final_score = validation.get("confluence_score", 0)
            if final_score < 60:
                logger.info(f"[Signal] {symbol} confluence too low ({final_score}) — skipping")
                return

            # EXECUTE TRADE
            logger.info(f"[Velora] Executing: {direction} {symbol} | Lots: {lots} | SL: {sl_tp['sl']} | TP: {sl_tp['tp2']} | Score: {final_score}")
            result = connector.place_order(
                symbol=symbol,
                order_type=direction,
                lots=lots,
                sl=sl_tp["sl"],
                tp=sl_tp["tp2"],
                comment=f"Velora {strategy.get('id','AI')} Score:{final_score}"
            )

            if result.get("success"):
                await db_logger.log_trade_opened(symbol, direction, lots, sl_tp, result, strategy, final_score)
                logger.success(f"[Velora] ✅ Trade placed: {direction} {symbol} ticket={result.get('ticket')}")
            else:
                logger.error(f"[Velora] ❌ Trade failed: {result.get('error')}")
                await db_logger.log_trade_failed(symbol, direction, result)

        except Exception as e:
            logger.exception(f"[Velora] Error analyzing {symbol}: {e}")

    async def _manage_open_trades(self):
        positions = connector.get_open_positions()
        account = connector.get_account()
        balance = account.get("balance", 0)

        for pos in positions:
            try:
                symbol = pos["symbol"]
                ticket = pos["ticket"]
                direction = pos["type"]
                current_price = connector.get_symbol_info(symbol)
                price = current_price.get("bid") if direction == "BUY" else current_price.get("ask")
                if not price:
                    continue

                profit_pips = (price - pos["open_price"]) * (1 if direction == "BUY" else -1) * 10000

                # Trailing stop: move SL to breakeven after +20 pips profit
                if profit_pips >= 20:
                    info = connector.get_symbol_info(symbol)
                    digits = info.get("digits", 5)
                    new_sl = round(pos["open_price"] + (0.0003 if direction == "BUY" else -0.0003), digits)
                    if (direction == "BUY" and new_sl > pos["sl"]) or (direction == "SELL" and new_sl < pos["sl"]):
                        if connector.modify_sl_tp(ticket, new_sl, pos["tp"]):
                            logger.info(f"[TrailingStop] {symbol} SL moved to breakeven+3 pips")

                # Force close if daily drawdown critical
                if balance > 0:
                    daily_loss_pct = abs(min(risk_manager.get_daily_pnl(), 0)) / balance
                    if daily_loss_pct >= config.MAX_DAILY_LOSS * 0.9:
                        if pos["profit"] < 0:
                            result = connector.close_trade(ticket)
                            if result.get("success"):
                                logger.warning(f"[RiskClose] Closed losing trade {ticket} — near daily limit")
                                risk_manager.record_trade_result(pos["profit"])
                                await db_logger.log_trade_closed(ticket, pos["profit"], "risk_limit")

            except Exception as e:
                logger.error(f"[TradeManager] Error managing ticket {ticket}: {e}")

    async def run_cycle(self):
        self.cycle_count += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"[Velora] Cycle #{self.cycle_count} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            # Step 1: Get market regime from DeepSeek
            account = connector.get_account()
            open_positions = connector.get_open_positions()
            market_snapshot = {
                "account": account,
                "open_trades": len(open_positions),
                "pairs_watching": config.DEFAULT_PAIRS,
                "cycle": self.cycle_count,
                "utc_hour": datetime.now(timezone.utc).hour
            }
            regime = await brain.analyze_market_regime(market_snapshot)
            self.last_regime = regime
            logger.info(f"[DeepSeek] Regime: {regime.get('regime')} | Confidence: {regime.get('confidence', 0):.0%} | Session: {regime.get('session_quality')}")

            if regime.get("session_quality") == "poor":
                logger.info("[Velora] Poor session quality — skipping signal generation this cycle")
                return

            # Step 2: Manage existing trades
            await self._manage_open_trades()

            # Step 3: Scan all pairs for signals
            for symbol in config.DEFAULT_PAIRS:
                if symbol in regime.get("avoid_pairs", []):
                    continue
                await self._analyze_pair(symbol, regime)
                await asyncio.sleep(1)  # rate limit

        except Exception as e:
            logger.exception(f"[Velora] Cycle error: {e}")

    async def run(self, interval_seconds: int = 300):
        if not await self.startup():
            return

        self.running = True
        logger.success("[Velora] 🚀 Autonomous trading started — scanning every 5 minutes")

        while self.running:
            await self.run_cycle()
            logger.info(f"[Velora] Next cycle in {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False
        connector.disconnect()
        logger.info("[Velora] Engine stopped")

engine = TradingEngine()
