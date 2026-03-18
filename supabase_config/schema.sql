-- Velora Trading Engine — Supabase Schema
-- Run this in Supabase SQL Editor once

-- ── Trades table ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trades (
  id              BIGSERIAL PRIMARY KEY,
  timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  candle_time     TIMESTAMPTZ,
  symbol          TEXT NOT NULL,
  price           NUMERIC(12, 5),
  decision        TEXT,
  reasons         TEXT,
  rr              NUMERIC(6, 2),
  position_size   NUMERIC(8, 2),
  status          TEXT,          -- EXECUTED, PAPER, ERROR, REJECTED
  ticket          BIGINT,        -- MT5 ticket number
  sl              NUMERIC(12, 5),
  tp              NUMERIC(12, 5),
  profit          NUMERIC(10, 2),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);

-- ── Engine events (heartbeat, kill switch, errors) ────────────────────────────
CREATE TABLE IF NOT EXISTS engine_events (
  id              BIGSERIAL PRIMARY KEY,
  type            TEXT NOT NULL,   -- HEARTBEAT, KILL_SWITCH_ACTIVATED, ERROR, ENGINE_START, etc.
  severity        TEXT DEFAULT 'info',
  message         TEXT,
  data            JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON engine_events(type);
CREATE INDEX IF NOT EXISTS idx_events_created ON engine_events(created_at DESC);

-- ── Audit journal ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
  id              BIGSERIAL PRIMARY KEY,
  event_type      TEXT NOT NULL,   -- TRADE, SYSTEM, ERROR, KILL_SWITCH
  symbol          TEXT,
  action          TEXT,
  details         JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Performance snapshots ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS performance_snapshots (
  id              BIGSERIAL PRIMARY KEY,
  date            DATE NOT NULL UNIQUE,
  balance         NUMERIC(12, 2),
  equity          NUMERIC(12, 2),
  daily_pnl       NUMERIC(12, 2),
  daily_trades    INTEGER DEFAULT 0,
  wins            INTEGER DEFAULT 0,
  losses          INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Row Level Security ────────────────────────────────────────────────────────
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE engine_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_snapshots ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (backend uses service key)
CREATE POLICY "service_role_all" ON trades FOR ALL USING (TRUE);
CREATE POLICY "service_role_all" ON engine_events FOR ALL USING (TRUE);
CREATE POLICY "service_role_all" ON audit_log FOR ALL USING (TRUE);
CREATE POLICY "service_role_all" ON performance_snapshots FOR ALL USING (TRUE);

-- ── Useful views ──────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW trade_stats AS
SELECT
  COUNT(*) FILTER (WHERE status = 'EXECUTED') AS total_executed,
  COUNT(*) FILTER (WHERE status = 'PAPER') AS total_paper,
  COUNT(*) FILTER (WHERE profit > 0 AND status = 'EXECUTED') AS wins,
  COUNT(*) FILTER (WHERE profit <= 0 AND status = 'EXECUTED') AS losses,
  ROUND(AVG(profit) FILTER (WHERE status = 'EXECUTED'), 2) AS avg_profit,
  ROUND(SUM(profit) FILTER (WHERE status = 'EXECUTED'), 2) AS total_pnl,
  ROUND(
    COUNT(*) FILTER (WHERE profit > 0 AND status = 'EXECUTED')::NUMERIC /
    NULLIF(COUNT(*) FILTER (WHERE status = 'EXECUTED'), 0) * 100, 1
  ) AS win_rate_pct
FROM trades;

-- ── RPC: last 30 days equity curve ────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_equity_curve(days_back INT DEFAULT 30)
RETURNS TABLE(date DATE, daily_pnl NUMERIC, cumulative_pnl NUMERIC) AS $$
  SELECT
    date,
    daily_pnl,
    SUM(daily_pnl) OVER (ORDER BY date) AS cumulative_pnl
  FROM performance_snapshots
  WHERE date >= CURRENT_DATE - days_back
  ORDER BY date;
$$ LANGUAGE SQL;
