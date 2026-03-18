"""
Phase 1 test gate — validates config, project structure, and root imports.
Run: python -m pytest tests/test_phase1_imports.py -v
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_velora_config_import():
    """Config loads without error and engine_mode has a valid value."""
    from backend.app.core.config import config
    assert config.engine_mode in ("paper", "live", "backtest")


def test_config_defaults():
    """Default values are safe for paper trading."""
    from backend.app.core.config import config
    assert config.risk_per_trade_pct <= 0.05      # Max 5% risk per trade
    assert config.max_daily_loss_pct <= 0.20       # Max 20% daily loss
    assert config.max_positions >= 1
    assert config.adx_trend_threshold > 0
    assert config.ema_fast < config.ema_slow       # EMA fast must be shorter than slow


def test_config_pairs_list():
    """pairs_list property returns at least one symbol."""
    from backend.app.core.config import config
    assert isinstance(config.pairs_list, list)
    assert len(config.pairs_list) >= 1


def test_backend_app_packages_exist():
    """All backend/app sub-packages are importable."""
    import importlib
    packages = [
        "backend.app",
        "backend.app.core",
        "backend.app.engine",
        "backend.app.execution",
        "backend.app.risk",
        "backend.app.strategies",
        "backend.app.ai",
        "backend.app.analytics",
        "backend.app.monitoring",
    ]
    for pkg in packages:
        mod = importlib.import_module(pkg)
        assert mod is not None, f"Package not importable: {pkg}"


def test_root_modules_still_importable():
    """Root compatibility shims: all original root modules must still import."""
    import config  # noqa
    import risk    # noqa
    import kill_switch  # noqa
    import session_filter  # noqa
    import news_filter    # noqa
    import indicators     # noqa
    import journal        # noqa


def test_sqlite_migrations_runner():
    """SQLite migrations runner imports and runs without error."""
    from backend.app.core.migrations import run_sqlite_migrations
    import tempfile
    import sqlite3

    # Create temp DB with trades table
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_db = f.name

    conn = sqlite3.connect(tmp_db)
    conn.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            direction TEXT,
            pnl REAL
        )
    """)
    conn.commit()
    conn.close()

    # Run migrations — should add columns without errors
    run_sqlite_migrations(tmp_db)

    # Verify columns were added
    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute("PRAGMA table_info(trades)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    import os
    os.unlink(tmp_db)

    assert "strategy_name" in columns
    assert "confidence" in columns
    assert "market_regime" in columns
    assert "exec_latency_ms" in columns
    assert "slippage_pips" in columns
    assert "account_id" in columns
