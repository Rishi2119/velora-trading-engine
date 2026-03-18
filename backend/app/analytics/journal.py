"""
Phase 14: Trade Journal and Supabase Resilient Sync.
Logs all trades to a local SQLite database, and pushes asynchronously 
to Supabase with an exponential backoff retry mechanism to ensure no data loss on network drops.
"""
import os
import sqlite3
import json
import logging
import asyncio
from typing import Dict, Any

from backend.app.core.config import config

logger = logging.getLogger(__name__)

class TradeJournal:
    """Records trade history and manages Supabase sync."""
    
    def __init__(self, db_path: str = "logs/trades.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    ticket INTEGER PRIMARY KEY,
                    symbol TEXT,
                    direction TEXT,
                    lots REAL,
                    entry_price REAL,
                    exit_price REAL,
                    sl REAL,
                    tp REAL,
                    pnl REAL,
                    strategy_name TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    synced_to_cloud BOOLEAN DEFAULT 0
                )
            """)
            
    async def log_trade(self, trade_data: Dict[str, Any]):
        """Logs a completed or opened trade, triggering an async push."""
        self._save_local(trade_data)
        
        # Fire and forget async push
        asyncio.create_task(self._push_to_supabase_with_retry(trade_data))
        
    def _save_local(self, trade_data: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO trades 
                (ticket, symbol, direction, lots, entry_price, exit_price, sl, tp, pnl, strategy_name, entry_time, exit_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data.get("ticket"),
                trade_data.get("symbol"),
                trade_data.get("direction"),
                trade_data.get("lots"),
                trade_data.get("entry_price"),
                trade_data.get("exit_price"),
                trade_data.get("sl"),
                trade_data.get("tp"),
                trade_data.get("pnl"),
                trade_data.get("strategy_name"),
                trade_data.get("entry_time"),
                trade_data.get("exit_time")
            ))
            
    def _mark_synced(self, ticket: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE trades SET synced_to_cloud = 1 WHERE ticket = ?", (ticket,))
            
    async def _push_to_supabase_with_retry(self, trade_data: Dict[str, Any], max_retries: int = 3):
        try:
            from supabase import create_client, Client
        except ImportError:
            logger.warning("Supabase package not installed. Skipping cloud sync.")
            return
            
        if not config.supabase_url or not config.supabase_key:
            logger.warning("Supabase credentials missing from config. Skipping cloud sync.")
            return
            
        client: Client = create_client(config.supabase_url, config.supabase_key)
        
        for attempt in range(1, max_retries + 1):
            try:
                loop = asyncio.get_running_loop()
                # Run the synchronous sync command in an executor
                response = await loop.run_in_executor(
                    None, 
                    lambda: client.table("trades").upsert(trade_data).execute()
                )
                
                logger.info(f"Successfully pushed trade {trade_data.get('ticket')} to Supabase.")
                self._mark_synced(trade_data.get("ticket"))
                return
                
            except Exception as e:
                delay = 2 ** attempt
                logger.error(f"Supabase push failed (Attempt {attempt}/{max_retries}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                
        logger.critical(f"Failed to push trade {trade_data.get('ticket')} to Supabase after {max_retries} attempts. Flagged as unsynced in SQLite.")

trade_journal = TradeJournal()
