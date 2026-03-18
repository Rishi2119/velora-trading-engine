"""
Phase 1D — SQLite migration runner.
Runs ALTER TABLE migrations safely (duplicate column errors are ignored).
Called by backend database startup.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

# All migrations are idempotent — safe to run multiple times
SQLITE_MIGRATIONS = [
    "ALTER TABLE trades ADD COLUMN strategy_name TEXT",
    "ALTER TABLE trades ADD COLUMN confidence INTEGER",
    "ALTER TABLE trades ADD COLUMN market_regime TEXT",
    "ALTER TABLE trades ADD COLUMN exec_latency_ms REAL",
    "ALTER TABLE trades ADD COLUMN slippage_pips REAL",
    "ALTER TABLE trades ADD COLUMN account_id TEXT",
]


def run_sqlite_migrations(db_path: str = "velora.db") -> None:
    """
    Apply all pending SQLite migrations.
    Duplicate-column errors are silently ignored (already migrated).
    """
    try:
        conn = sqlite3.connect(db_path)
        for sql in SQLITE_MIGRATIONS:
            try:
                conn.execute(sql)
                logger.debug(f"Migration applied: {sql[:60]}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    pass  # Already applied — OK
                else:
                    logger.warning(f"Migration skipped ({e}): {sql[:60]}")
        conn.commit()
        conn.close()
        logger.info("SQLite migrations complete.")
    except Exception as e:
        logger.error(f"SQLite migration error: {e}")
