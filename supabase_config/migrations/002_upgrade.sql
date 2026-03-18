-- supabase/migrations/002_upgrade.sql
-- Phase 1D: Upgrade schema for Velora trading engine v2
-- All statements are idempotent — safe to run multiple times.

-- ── Extend trades table ───────────────────────────────────────────────────────
ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy_name TEXT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS confidence     INTEGER;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS market_regime  TEXT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS exec_latency_ms FLOAT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS slippage_pips   FLOAT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS account_id      TEXT;

-- ── Multi-account support ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trading_accounts (
    id               TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    user_id          TEXT NOT NULL DEFAULT 'default',
    broker           TEXT NOT NULL,
    login            BIGINT NOT NULL,
    server           TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    status           TEXT DEFAULT 'active' CHECK (status IN ('active','paused','error')),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    last_connected   TIMESTAMPTZ,
    UNIQUE(user_id, login)
);

-- ── Strategy performance tracking ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategy_performance (
    id             BIGSERIAL PRIMARY KEY,
    strategy_name  TEXT NOT NULL,
    evaluated_at   TIMESTAMPTZ DEFAULT NOW(),
    total_trades   INT DEFAULT 0,
    win_rate       FLOAT,
    profit_factor  FLOAT,
    sharpe_ratio   FLOAT,
    max_drawdown   FLOAT,
    expectancy     FLOAT,
    weight         FLOAT DEFAULT 1.0,
    period_days    INT DEFAULT 30
);

-- ── Backtest results ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS backtest_results (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    run_at        TIMESTAMPTZ DEFAULT NOW(),
    strategy_name TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    timeframe     TEXT NOT NULL,
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    total_trades  INT,
    win_rate      FLOAT,
    sharpe_ratio  FLOAT,
    sortino_ratio FLOAT,
    max_drawdown  FLOAT,
    profit_factor FLOAT,
    expectancy    FLOAT,
    net_pnl       FLOAT,
    equity_curve  JSONB,
    parameters    JSONB
);

-- ── Execution quality metrics ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS execution_metrics (
    id            BIGSERIAL PRIMARY KEY,
    recorded_at   TIMESTAMPTZ DEFAULT NOW(),
    symbol        TEXT,
    latency_ms    FLOAT,
    slippage_pips FLOAT,
    spread        FLOAT,
    retcode       INT,
    rejected      BOOL DEFAULT FALSE
);

-- ── Copy trading signals ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS copy_signals (
    id                BIGSERIAL PRIMARY KEY,
    emitted_at        TIMESTAMPTZ DEFAULT NOW(),
    master_account_id TEXT NOT NULL,
    symbol            TEXT NOT NULL,
    direction         TEXT NOT NULL,
    lots              FLOAT NOT NULL,
    entry_price       FLOAT NOT NULL,
    sl                FLOAT,
    tp                FLOAT,
    status            TEXT DEFAULT 'pending'
);

-- ── Realtime publications ─────────────────────────────────────────────────────
DO $$
BEGIN
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE strategy_performance;
    EXCEPTION WHEN others THEN NULL;
    END;
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE execution_metrics;
    EXCEPTION WHEN others THEN NULL;
    END;
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE copy_signals;
    EXCEPTION WHEN others THEN NULL;
    END;
END $$;

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_trades_strategy  ON trades(strategy_name);
CREATE INDEX IF NOT EXISTS idx_trades_account   ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_strat_name       ON strategy_performance(strategy_name);
CREATE INDEX IF NOT EXISTS idx_exec_time        ON execution_metrics(recorded_at DESC);
