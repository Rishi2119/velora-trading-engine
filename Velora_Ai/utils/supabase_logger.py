# // turbo
from supabase import create_client, Client
from loguru import logger
from config.settings import config
from datetime import datetime, timezone


class SupabaseLogger:
    def __init__(self):
        self.client: Client | None = None
        self._connect()

    def _connect(self):
        try:
            if config.SUPABASE_URL and config.SUPABASE_KEY:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                logger.success("[Supabase] Connected")
        except Exception as e:
            logger.warning(f"[Supabase] Connection failed (will log to file only): {e}")

    async def _insert(self, table: str, data: dict):
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        if self.client:
            try:
                self.client.table(table).insert(data).execute()
            except Exception as e:
                logger.error(f"[Supabase] Insert error ({table}): {e}")
        logger.debug(f"[Log] {table}: {data}")

    async def log_event(self, event_type: str, action: str, payload: dict):
        await self._insert("velora_events", {"type": event_type, "action": action, "payload": str(payload)})

    async def log_trade_opened(self, symbol, direction, lots, sl_tp, result, strategy, score):
        await self._insert("velora_trades", {
            "ticket": result.get("ticket"), "symbol": symbol, "direction": direction,
            "lots": lots, "entry": result.get("price"), "sl": sl_tp["sl"],
            "tp": sl_tp["tp2"], "strategy_id": strategy.get("id"),
            "strategy_name": strategy.get("name"), "confluence_score": score,
            "status": "open"
        })

    async def log_trade_closed(self, ticket, pnl, reason):
        if self.client:
            try:
                self.client.table("velora_trades").update({
                    "pnl": pnl, "status": "closed", "close_reason": reason,
                    "closed_at": datetime.now(timezone.utc).isoformat()
                }).eq("ticket", ticket).execute()
            except Exception as e:
                logger.error(f"[Supabase] Close update error: {e}")

    async def log_signal_rejected(self, symbol, direction, validation):
        await self._insert("velora_signals_rejected", {
            "symbol": symbol, "direction": direction,
            "reason": validation.get("rejection_reason"),
            "confluence_score": validation.get("confluence_score", 0)
        })

    async def log_trade_failed(self, symbol, direction, result):
        await self._insert("velora_errors", {
            "symbol": symbol, "direction": direction,
            "error": result.get("error"), "context": "trade_execution"
        })

db_logger = SupabaseLogger()
